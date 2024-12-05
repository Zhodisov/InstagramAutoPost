
import logging
import datetime
import traceback
from database.database import SessionLocal
from database.models import LogEntry

class DBHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        if record.exc_info:
            exc_info_formatted = ''.join(traceback.format_exception(*record.exc_info))
        else:
            exc_info_formatted = None

        log_entry = LogEntry(
            timestamp=datetime.datetime.fromtimestamp(record.created),
            level=record.levelname,
            message=record.getMessage(),
            logger_name=record.name,
            filename=record.filename,
            function_name=record.funcName,
            line_number=record.lineno,
            exc_info=exc_info_formatted
        )

        db = SessionLocal()
        try:
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()
