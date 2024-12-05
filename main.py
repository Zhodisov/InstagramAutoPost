import logging
from queue import Queue
import random
import time
from pathlib import Path
import threading
import asyncio

from config.config_loader import load_config, load_accounts_to_monitor
from instagram.client import InstagramClient
from instagram.downloader import downloaduploadclip
from instagram.uploader import clipcount
from database.models import ClipInfo
from database.database import SessionLocal
from utils.notifications import discord_webhook
from utils.logger import jsonlog

from app import app as fastapi_app, manager

def main():
    log_queue = Queue()
    loop_queue = Queue()
    def start_fastapi_server():
        import uvicorn
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop_queue.put(loop)
        fastapi_app.state.log_queue = log_queue
        uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    fastapi_thread = threading.Thread(target=start_fastapi_server, daemon=True)
    fastapi_thread.start()
    time.sleep(2)
    manager.loop = loop_queue.get()
    logger = jsonlog(level=logging.INFO, ws_queue=log_queue)
    cd = load_config()
    credentials = cd["instagram_credentials"]
    upload_settings = cd["upload_settings"]
    d = Path("downloads")
    d.mkdir(parents=True, exist_ok=True)
    instagram_client = InstagramClient(credentials, logger)
    client = instagram_client.client
    accounts_data = load_accounts_to_monitor()

    try:
        user_id = client.user_id_from_username(credentials["INSTAGRAM_USERNAME"])
    except Exception as e:
        return

    icp = clipcount(client, user_id)

    uc = 0
    max_uploads_per_day = upload_settings["max_uploads_per_day"]
    upload_cycle_count = 0
    max_cycle_videos = upload_settings["max_cycle_videos"]
    interval_between_uploads = upload_settings["interval_between_uploads_seconds"]
    pause_duration = upload_settings["pause_duration_seconds"]

    while uc < max_uploads_per_day:
        accounts = accounts_data["accounts"]
        random.shuffle(accounts)

        for username in accounts:
            clips = instagram_client.get_all_clips(username)
            to_download = []

            max_clips_per_account = 3
            for clip in clips:
                media_pk = str(clip.pk)
                if not clip_already_processed(media_pk):
                    to_download.append(clip)
                if len(to_download) >= max_clips_per_account:
                    break

            if not to_download:
                continue

            for clip in to_download:
                if uc >= max_uploads_per_day:
                    break

                if upload_cycle_count >= max_cycle_videos:
                    time.sleep(pause_duration)
                    upload_cycle_count = 0

                success = downloaduploadclip(
                    client, clip, d, icp, user_id, uc,
                    "config_files/description.json", credentials, logger
                )

                if success:
                    uc += 1
                    upload_cycle_count += 1
                    icp += 1
                    clip_info = get_clip_info(media_pk=clip.pk)

                    data = {
                        "type": "new_clip",
                        "uc": uc,
                        "message": f"📤 Vidéo {uc}/{max_uploads_per_day} uploadée avec succès.",
                        "clip_info": clip_to_dict(clip_info)
                    }
                    #manager.loop = asyncio.get_event_loop()
                    future = asyncio.run_coroutine_threadsafe(manager.send_json(data), manager.loop)
                    webhook_url = credentials.get("DISCORD_WEBHOOK_URL")
                    if webhook_url:
                        discord_webhook(
                            title="Vidéo uploadée",
                            description=data["message"],
                            color=3066993,
                            webhook_url=webhook_url
                        )

                    time.sleep(interval_between_uploads)
                else:
                    time.sleep(interval_between_uploads)

            if uc >= max_uploads_per_day:
                break

def clip_already_processed(media_pk):
    db = SessionLocal()
    try:
        existing_clip = db.query(ClipInfo).filter(ClipInfo.media_pk == str(media_pk)).first()
        return existing_clip is not None
    finally:
        db.close()

def get_clip_info(media_pk):
    db = SessionLocal()
    try:
        clip_info = db.query(ClipInfo).filter(ClipInfo.media_pk == str(media_pk)).first()
        return clip_info
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

if __name__ == "__main__":
    main()
