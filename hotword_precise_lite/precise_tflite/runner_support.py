import numpy as np

from abc import abstractmethod, ABCMeta
from threading import Event

class Engine(object):
    def __init__(self, chunk_size=2048):
        self.chunk_size = chunk_size

    def start(self):
        pass

    def stop(self):
        pass

    def get_prediction(self, chunk):
        raise NotImplementedError


class Runner(metaclass=ABCMeta):
    @abstractmethod
    def predict(self, inputs: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def run(self, inp: np.ndarray) -> float:
        pass


class ReadWriteStream(object):
    """
    Class used to support writing binary audio data at any pace,
    optionally chopping when the buffer gets too large
    """
    def __init__(self, s=b'', chop_samples=-1):
        self.buffer = s
        self.write_event = Event()
        self.chop_samples = chop_samples

    def __len__(self):
        return len(self.buffer)

    def read(self, n=-1, timeout=None):
        if n == -1:
            n = len(self.buffer)
        if 0 < self.chop_samples < len(self.buffer):
            samples_left = len(self.buffer) % self.chop_samples
            self.buffer = self.buffer[-samples_left:]
        return_time = 1e10 if timeout is None else (
                timeout + time.time()
        )
        while len(self.buffer) < n:
            self.write_event.clear()
            if not self.write_event.wait(return_time - time.time()):
                return b''
        chunk = self.buffer[:n]
        self.buffer = self.buffer[n:]
        return chunk

    def write(self, s):
        self.buffer += s
        self.write_event.set()

    def flush(self):
        """Makes compatible with sys.stdout"""
        pass
