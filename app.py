from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import asyncio

from database.database import SessionLocal
from database.models import ClipInfo, LogEntry
from sqlalchemy.orm import Session
from sqlalchemy import func
from queue import Queue
import time

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
log_queue = Queue()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()
        self.loop = asyncio.get_event_loop()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            self.active_connections.remove(websocket)

    async def send_json(self, message: dict):
        async with self.lock:
            for connection in self.active_connections:
                await connection.send_json(message)

    async def send_log(self, message: str):
        async with self.lock:
            disconnected_connections = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    disconnected_connections.append(connection)
            for connection in disconnected_connections:
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            if not log_queue.empty():
                msg = log_queue.get()
                await manager.send_log(msg)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.get("/api/clips")
async def get_clips(
    original_username: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    page: int = Query(1),
    page_size: int = Query(10)
):
    db = SessionLocal()
    try:
        query = db.query(ClipInfo)
        if original_username:
            query = query.filter(ClipInfo.original_username == original_username)
        if start_date:
            query = query.filter(ClipInfo.download_date >= start_date)
        if end_date:
            query = query.filter(ClipInfo.download_date <= end_date)
        total = query.count()
        clips = query.order_by(ClipInfo.download_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
        clips_data = [clip_to_dict(clip) for clip in clips]
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "clips": clips_data
        }
    finally:
        db.close()

def clip_to_dict(clip):
    return {
        "media_pk": clip.media_pk,
        "download_date": clip.download_date.isoformat(),
        "original_username": clip.original_username,
        "description": clip.description,
        "video_url": clip.video_url,
        "local_file_path": clip.local_file_path,
        "upload_status": clip.upload_status,
        "upload_date": clip.upload_date.isoformat() if clip.upload_date else None,
        "additional_data": clip.additional_data
    }

@app.get("/api/stats/clips-per-day")
async def gpd(start_date: Optional[str] = None, end_date: Optional[str] = None):
    db: Session = SessionLocal()
    try:
        query = db.query(
            func.date(ClipInfo.download_date).label('date'),
            func.count(ClipInfo.id).label('count')
        ).group_by(func.date(ClipInfo.download_date)).order_by(func.date(ClipInfo.download_date))

        if start_date:
            query = query.filter(ClipInfo.download_date >= start_date)
        if end_date:
            query = query.filter(ClipInfo.download_date <= end_date)

        result = query.all()
        return [{"date": str(row.date), "count": row.count} for row in result]
    finally:
        db.close()
@app.get("/api/stats/logs-per-level")
async def gplg():
    db: Session = SessionLocal()
    try:
        query = db.query(
            LogEntry.level,
            func.count(LogEntry.id).label('count')
        ).group_by(LogEntry.level)

        result = query.all()
        return [{"level": row.level, "count": row.count} for row in result]
    finally:
        db.close()
@app.get("/api/logs")
async def get_logs(
    request: Request,
    level: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    db: Session = SessionLocal()
    try:
        query = db.query(LogEntry)

        if level:
            query = query.filter(LogEntry.level == level.upper())

        total_logs = query.count()
        logs = query.order_by(LogEntry.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()

        logs_data = [log.to_dict() for log in logs]

        return {
            "total": total_logs,
            "page": page,
            "page_size": page_size,
            "logs": logs_data
        }
    finally:
        db.close()

@app.get("/logs", response_class=HTMLResponse)
async def logs(request: Request):
    return templates.TemplateResponse('logs.html', {'request': request})

script_running = False

@app.post("/api/script/start")
async def start_script():
    global script_running
    if not script_running:
        script_running = True
        return {"status": "Script démarré"}
    else:
        return {"status": "Script déjà en cours d'exécution"}

@app.post("/api/script/stop")
async def stop_script():
    global script_running
    if script_running:
        script_running = False
        return {"status": "Script m"}
    else:
        return {"status": "Script e"}

@app.get("/api/stats/summary")
async def gstsm():
    db: Session = SessionLocal()
    try:
        total_downloaded = db.query(func.count(ClipInfo.id)).scalar()
        total_uploaded = db.query(func.count(ClipInfo.id)).filter(ClipInfo.upload_status == 'uploaded').scalar()
        upload_success_rate = (total_uploaded / total_downloaded * 100) if total_downloaded else 0

        return {
            "total_downloaded": total_downloaded,
            "total_uploaded": total_uploaded,
            "upload_success_rate": f"{upload_success_rate:.2f}%"
        }
    finally:
        db.close()

@app.get("/api/stats/downloads-uploads-per-day")
async def gduplday():
    db: Session = SessionLocal()
    try:
        download_query = db.query(
            func.date(ClipInfo.download_date).label('date'),
            func.count(ClipInfo.id).label('downloads')
        ).group_by(func.date(ClipInfo.download_date)).subquery()

        upload_query = db.query(
            func.date(ClipInfo.upload_date).label('date'),
            func.count(ClipInfo.id).label('uploads')
        ).filter(ClipInfo.upload_status == 'uploaded').group_by(func.date(ClipInfo.upload_date)).subquery()

        query = db.query(
            download_query.c.date,
            download_query.c.downloads,
            func.coalesce(upload_query.c.uploads, 0).label('uploads')
        ).outerjoin(upload_query, download_query.c.date == upload_query.c.date).order_by(download_query.c.date)

        result = query.all()
        return [{"date": str(row.date), "downloads": row.downloads, "uploads": row.uploads} for row in result]
    finally:
        db.close()

@app.get("/api/stats/processing-time-per-day")
async def gproc():
    db: Session = SessionLocal()
    try:
        query = db.query(
            func.date(ClipInfo.download_date).label('date'),
            func.avg(ClipInfo.processing_time).label('average_processing_time')
        ).filter(ClipInfo.processing_time != None).group_by(func.date(ClipInfo.download_date)).order_by(func.date(ClipInfo.download_date))

        result = query.all()
        return [{"date": str(row.date), "average_processing_time": row.average_processing_time} for row in result]
    finally:
        db.close()

@app.get("/api/media/recent")
async def grecenmd():
    db: Session = SessionLocal()
    try:
        media = db.query(ClipInfo).order_by(ClipInfo.download_date.desc()).limit(20).all()
        media_list = [clip_to_dict(clip) for clip in media]
        return {"media": media_list}
    finally:
        db.close()