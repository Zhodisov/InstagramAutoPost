import logging
from logging.handlers import RotatingFileHandler
import os
from utils.db_logger import DBHandler
from utils.websocket_logger import WebSocketHandler

def jsonlog(name=None, level=logging.INFO, ws_queue=None):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter('{"asctime": "%(asctime)s", "name": "%(name)s", "levelname": "%(levelname)s", "message": "%(message)s"}')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        log_file = os.path.join('logs', 'app.log')
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        db_handler = DBHandler()
        db_handler.setLevel(level)
        logger.addHandler(db_handler)

        if ws_queue:
            ws_handler = WebSocketHandler(ws_queue)
            ws_handler.setLevel(level)
            ws_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            ws_handler.setFormatter(ws_formatter)
            logger.addHandler(ws_handler)

    return logger
