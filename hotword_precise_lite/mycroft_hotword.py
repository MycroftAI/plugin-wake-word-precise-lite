
# environment specific 
import numpy as np
from time import time
from mycroft.configuration import Configuration, LocalConf, USER_CONFIG
from .network_runner import ReadWriteStream, Listener, Engine
from .precise_tflite.util import buffer_to_audio

class ListenerEngine(Engine):
    def __init__(self, listener, chunk_size=2048):
        Engine.__init__(self, chunk_size)
        self.get_prediction = listener.update

class TFLiteEngine:
    def __init__(self, key_phrase="hey mycroft", config=None, lang="en-us"):
        self.key_phrase = str(key_phrase).lower()
        # rough estimate 1 phoneme per 2 chars
        self.num_phonemes = len(key_phrase) / 2 + 1
        if config is None:
            config = Configuration.get().get("hot_words", {})
            config = config.get(self.key_phrase, {})
        self.config = config
        self.listener_config = Configuration.get().get("listener", {})
        self.lang = str(self.config.get("lang", lang)).lower()

    def found_wake_word(self, frame_data):
        return False

    def update(self, chunk):
        pass

    def stop(self):
        """ Perform any actions needed to shut down the hot word engine.

            This may include things such as unload loaded data or shutdown
            external processess.
        """
        pass

class TFLiteHotWord(TFLiteEngine):
    """TFLite supports any tflite model regardless of wake 
        word that meets the precise vectorization criteria"""
    def __init__(self, key_phrase="hey mycroft", config=None, lang="en-us"):
        super().__init__(key_phrase, config, lang)

        def on_activation():
            self.has_found = True

        config = Configuration.get().get("hotwords", {})
        config = config.get("hey mycroft", {})
        self.sensitivity = config.get("sensitivity", 0.8)

        params = {}
        params['sensitivity'] = self.sensitivity
        params['trigger_level'] = config.get("trigger_level", 4)
        params['chunk_size'] = config.get("chunk_size", 2048)
        params['local_model'] = config.get("local_model_file", None)
        params['on_activation'] = on_activation
        params['on_prediction'] = self.on_prediction

        self.listener = Listener(params['local_model'], params['chunk_size'])
        self.engine = ListenerEngine(self.listener, params['chunk_size'])
        params['engine'] = self.engine
        self.engine.get_prediction = self.get_prediction
        self.listener.runner.set_params(params)

        self.ww_debounce = config.get("ww_debounce", 3)
        self.audio_buffer = np.zeros(self.listener.pr.buffer_samples, dtype=float)
        self.has_found = False
        self.stream = ReadWriteStream()
        self.last_rec = time()

        self.run()

    def update(self, chunk):
        self.stream.write(chunk)

    def found_wake_word(self, frame_data):
        if self.has_found:
            self.has_found = False
            return True
        return False

    def stop(self):
        if self.listener.runner:
            self.listener.runner.stop()

    def on_prediction(self, conf):
        if conf and conf > self.sensitivity:
            # debounce
            if time() - self.last_rec > self.ww_debounce:
                self.last_rec = time()
                self.found_wake_word(None)

    def get_prediction(self, chunk):
        audio = buffer_to_audio(chunk)
        self.audio_buffer = np.concatenate((self.audio_buffer[len(audio):], audio))
        return self.listener.update(chunk)

    def run(self):
        self.listener.runner.start()


