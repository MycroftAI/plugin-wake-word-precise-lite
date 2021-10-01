# Copyright 2019 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import atexit
import numpy as np
import tflite_runtime.interpreter as tflite

from typing import *
from typing import BinaryIO
from os.path import splitext
from importlib import import_module
from threading import Thread, Event

from .precise_tflite.util import buffer_to_audio
from .precise_tflite.model import load_precise_model
from .precise_tflite.params import inject_params, pr
from .precise_tflite.threshold_decoder import ThresholdDecoder
from .precise_tflite.vectorization import vectorize_raw, add_deltas
from .precise_tflite.runner_support import Engine, Runner, ReadWriteStream

class TriggerDetector:
    """
    Reads predictions and detects activations
    This prevents multiple close activations from occurring when
    the predictions look like ...!!!..!!...
    """
    def __init__(self, chunk_size, sensitivity=0.5, trigger_level=3):
        self.chunk_size = chunk_size
        self.sensitivity = sensitivity
        self.trigger_level = trigger_level
        self.activation = 0

    def update(self, prob):
        # type: (float) -> bool
        """Returns whether the new prediction caused an activation"""
        chunk_activated = False
        if prob:
            chunk_activated = prob > 1.0 - self.sensitivity

        if chunk_activated or self.activation < 0:
            self.activation += 1
            has_activated = self.activation > self.trigger_level
            if has_activated or chunk_activated and self.activation < 0:
                self.activation = -(8 * 2048) // self.chunk_size

            if has_activated:
                return True
        elif self.activation > 0:
            self.activation -= 1
        return False


class TFLiteRunner(Runner):
    def __init__(self, model_name):
        self.model_file = model_name
        self.pa = None
        self.thread = None
        self.running = False
        self.is_paused = False
        self.stream = None
        atexit.register(self.stop)

    def set_params(self, params):
        self.model_file = params['local_model']
        self.chunk_size = params['chunk_size']
        self.engine = params['engine']
        self.on_prediction = params['on_prediction']
        self.on_activation = params['on_activation']
        self.trigger_level = params['trigger_level']
        self.sensitivity = params['sensitivity']

    def run(self, inp: np.ndarray) -> float:
        return self.predict(inp[np.newaxis])[0][0]

    def _wrap_stream_read(self, stream):
        """pyaudio.Stream.read takes samples as n, not bytes
           so read(n) should be read(n // sample_depth)"""
        import pyaudio
        if getattr(stream.read, '__func__', None) is pyaudio.Stream.read:
            stream.read = lambda x: pyaudio.Stream.read(stream, x // 2, False)

    def start(self):
        self.interpreter = tflite.Interpreter(model_path=self.model_file)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.detector = TriggerDetector(self.chunk_size, self.sensitivity, self.trigger_level)

        """Start listening from stream"""
        if self.stream is None:
            from pyaudio import PyAudio, paInt16
            self.pa = PyAudio()
            self.stream = self.pa.open(
                16000, 1, paInt16, True, frames_per_buffer=self.chunk_size
            )

        self._wrap_stream_read(self.stream)

        while self.engine is None:
            print("wait engine set")
            time.sleep(3)

        self.engine.start()
        self.running = True
        self.is_paused = False
        self.thread = Thread(target=self._handle_predictions, daemon=True)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop listening and close stream"""
        if self.thread:
            self.running = False
            if isinstance(self.stream, ReadWriteStream):
                self.stream.write(b'\0' * self.chunk_size)
            self.thread.join()
            self.thread = None

        self.engine.stop()

        if self.pa:
            self.pa.terminate()
            self.stream.stop_stream()
            self.stream = self.pa = None

    def pause(self):
        self.is_paused = True

    def play(self):
        self.is_paused = False

    def predict(self, inputs: np.ndarray):
        # Format output to match Keras's model.predict output
        count = 0
        output_data = np.ndarray((inputs.shape[0],1), dtype=np.float32)
        
        # Support for multiple inputs
        for input in inputs:
          # Format as float32. Add a wrapper dimension.
          current = np.array([input]).astype(np.float32)
          
          # Load data, run inference and extract output from tensor
          self.interpreter.set_tensor(self.input_details[0]['index'], current)
          self.interpreter.invoke()
          output_data[count] = self.interpreter.get_tensor(self.output_details[0]['index'])
          count += 1
          
        return output_data

    def _handle_predictions(self):
        """Continuously check for recognition"""
        while self.running:
            chunk = self.stream.read(self.chunk_size)

            if self.is_paused:
                continue

            prob = self.engine.get_prediction(chunk)

            self.on_prediction(prob)
            if self.detector.update(prob):
                self.on_activation()


class Listener:
    """Listener that preprocesses audio into MFCC vectors and executes neural networks"""
    def __init__(self, model_name: str, chunk_size: int = -1, runner_cls: type = None):
        self.window_audio = np.array([])
        self.pr = inject_params(model_name)
        self.mfccs = np.zeros((self.pr.n_features, self.pr.n_mfcc))
        self.chunk_size = chunk_size
        runner_cls = runner_cls or self.find_runner(model_name)
        self.runner = runner_cls(model_name)
        self.threshold_decoder = ThresholdDecoder(self.pr.threshold_config, pr.threshold_center)

    @staticmethod
    def find_runner(model_name: str) -> Type[Runner]:
        runners = {
            '.tflite': TFLiteRunner
        }
        ext = splitext(model_name)[-1]
        if ext not in runners:
            raise ValueError('File extension of ' + model_name + ' must be: ' + str(list(runners)))
        return runners[ext]

    def clear(self):
        self.window_audio = np.array([])
        self.mfccs = np.zeros((self.pr.n_features, self.pr.n_mfcc))

    def update_vectors(self, stream: Union[BinaryIO, np.ndarray, bytes]) -> np.ndarray:
        if isinstance(stream, np.ndarray):
            buffer_audio = stream
        else:
            if isinstance(stream, (bytes, bytearray)):
                chunk = stream
            else:
                chunk = stream.read(self.chunk_size)
            if len(chunk) == 0:
                raise EOFError
            buffer_audio = buffer_to_audio(chunk)

        self.window_audio = np.concatenate((self.window_audio, buffer_audio))

        if len(self.window_audio) >= self.pr.window_samples:
            new_features = vectorize_raw(self.window_audio)
            self.window_audio = self.window_audio[len(new_features) * self.pr.hop_samples:]
            if len(new_features) > len(self.mfccs):
                new_features = new_features[-len(self.mfccs):]
            self.mfccs = np.concatenate((self.mfccs[len(new_features):], new_features))

        return self.mfccs

    def update(self, stream: Union[BinaryIO, np.ndarray, bytes]) -> float:
        mfccs = self.update_vectors(stream)
        if self.pr.use_delta:
            mfccs = add_deltas(mfccs)
        raw_output = self.runner.run(mfccs)
        return self.threshold_decoder.decode(raw_output)

