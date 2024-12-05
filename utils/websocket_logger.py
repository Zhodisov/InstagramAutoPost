import logging
from queue import Queue

class WebSocketHandler(logging.Handler):
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self.queue.put_nowait(msg)
        except Exception:
            pass
