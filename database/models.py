from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ClipInfo(Base):
    __tablename__ = 'clips'

    id = Column(Integer, primary_key=True, index=True)
    media_pk = Column(String, unique=True, index=True)
    download_date = Column(DateTime, default=datetime.utcnow)
    original_username = Column(String)
    description = Column(String)
    video_url = Column(Text)
    local_file_path = Column(String)
    upload_status = Column(String)
    upload_date = Column(DateTime)
    additional_data = Column(JSON)
class LogEntry(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(50))
    message = Column(Text)
    logger_name = Column(String(255))
    filename = Column(String(255))
    function_name = Column(String(255))
    line_number = Column(Integer)
    exc_info = Column(Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'message': self.message,
            'logger_name': self.logger_name,
            'filename': self.filename,
            'function_name': self.function_name,
            'line_number': self.line_number,
            'exc_info': self.exc_info,
        }