import logging
import os
import random
import threading
import time
import json
import requests  
from moviepy.editor import VideoFileClip

import yt_dlp

from instagram.uploader import (
    noteuploader,
    clipstory,
    cliplocation,
    uploadphoto,
    uploadalbum,
    clipmusic
)
from database.models import ClipInfo
from database.database import SessionLocal
from utils.notifications import discord_webhook

def delayed_delete(path, delay, logger):
    time.sleep(delay)
    try:
        os.remove(path)
    except Exception as e:
        pass

def downloaduploadclip(
    client, clip, download_folder, initial_clip_count, user_id, uploaded_count,
    DESCRIPTION, credentials, logger
):
    media_pk = str(clip.pk)
    start_time = time.time()
    today = time.strftime("%Y-%m-%dT%H:%M:%S")


    with SessionLocal() as db:
        existing_clip = db.query(ClipInfo).filter(ClipInfo.media_pk == media_pk).first()
        if existing_clip:
            return False

    try:
        media_info = client.media_info(clip.pk)
        media_type = media_info.media_type

        original_post_date = media_info.taken_at.strftime("%Y-%m-%dT%H:%M:%S") if media_info.taken_at else None
        view_count = getattr(media_info, 'view_count', 0)
        like_count = getattr(media_info, 'like_count', 0)
        location = media_info.location.name if media_info.location else None
        original_caption = media_info.caption_text
        original_user_id = media_info.user.pk
        comment_count = getattr(media_info, 'comment_count', 0)
        original_username = media_info.user.username
        description = randomdesc(DESCRIPTION)
        video_url = str(media_info.video_url) if media_type == 2 and media_info.video_url else None 
        local_file_path = str(download_folder)

        music_canonical_id = None
        if hasattr(media_info, 'clips_metadata') and media_info.clips_metadata:
            music_canonical_id = media_info.clips_metadata.get('music_canonical_id')

        if media_type == 1:
            success = process_image(
                client, media_info, download_folder, description, logger
            )
            downloaded_clip_path = None
        elif media_type == 2:
            success, downloaded_clip_path = process_video(
                client, media_info, download_folder, description, logger, music_canonical_id
            )
        elif media_type == 8:
            success = process_album(
                client, media_info, download_folder, description, logger
            )
            downloaded_clip_path = None
        else:
            return False

        if success:
            processing_time = time.time() - start_time
            additional_data = json.dumps({
                "original_post_date": original_post_date,
                "view_count": view_count,
                "like_count": like_count,
                "location": location,
                "original_caption": original_caption,
                "original_user_id": original_user_id,
                "media_type": media_type,
                "comment_count": comment_count,
                "processing_time": processing_time,
                "music_canonical_id": music_canonical_id
            })
            clip_info = ClipInfo(
                media_pk=media_pk,
                download_date=today,
                original_username=original_username,
                description=description,
                video_url=video_url,
                local_file_path=local_file_path,
                upload_status="uploaded",
                upload_date=time.strftime("%Y-%m-%dT%H:%M:%S"),
                additional_data=additional_data
            )
            db.add(clip_info)
            db.commit()

            webhook_url = credentials.get("DISCORD_WEBHOOK_URL")
            if webhook_url:
                discord_webhook(
                    title="Медиа успешно загружено",
                    description=f"Медиа {media_pk} загружено от @{original_username}",
                    color=3066993,
                    webhook_url=webhook_url
                )

                if media_type == 2:
                    story_upload_success = clipstory(client, downloaded_clip_path, original_username, media_pk)
                    
                    if clip_info.additional_data is None:
                        clip_info.additional_data = {}
                    elif isinstance(clip_info.additional_data, str):
                        clip_info.additional_data = json.loads(clip_info.additional_data)
                    
                    clip_info.additional_data['story_upload_status'] = 'success' if story_upload_success else 'failed'
                    db.commit()
                    discord_webhook(
                        title="История загружена",
                        description=f"Клип {media_pk} добавлен в историю для @{original_username}",
                        color=15844367,
                        webhook_url=webhook_url
                    )
                    time.sleep(6)

            return True
        else:
            return False

    except Exception as e:
        return False

def process_image(client, media_info, download_folder, description, logger):
    media_pk = str(media_info.pk)
    try:
        image_url = media_info.thumbnail_url

        image_extension = image_url.split('?')[0].split('.')[-1]
        downloaded_image_path = os.path.join(download_folder, f"{media_pk}.{image_extension}")

        response = requests.get(image_url)
        with open(downloaded_image_path, 'wb') as f:
            f.write(response.content)

        upload_success = uploadphoto(
            client,
            downloaded_image_path,
            description
        )
        if upload_success:
            os.remove(downloaded_image_path)
            return True
        else:
            return False

    except Exception as e:
        return False
def process_video(client, media_info, download_folder, description, logger, music_canonical_id=None):
    media_pk = str(media_info.pk)
    try:
        video_url = str(media_info.video_url)

        downloaded_clip_path = os.path.join(download_folder, f"{media_pk}.mp4")

        ydl_opts = {
            'outtmpl': downloaded_clip_path,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        if not os.path.isfile(downloaded_clip_path):
            return False, None
        try:
            clip_video = VideoFileClip(downloaded_clip_path)
            duration = clip_video.duration
            clip_video.reader.close()
            clip_video.audio.reader.close_proc()
        except Exception as e:
            return False, None

        if duration > 15:
            if os.path.exists(downloaded_clip_path):
                os.remove(downloaded_clip_path)
            return False, None

        track = None
        if music_canonical_id:
            try:
                track = client.track_info_by_canonical_id(music_canonical_id)
            except Exception as e:
                track = None

        if track:
            upload_success = clipmusic(
                client, downloaded_clip_path, description, track
            )
        else:
            upload_success = cliplocation(
                client, downloaded_clip_path, description
            )

        if upload_success:
            return True, downloaded_clip_path
        else:
            return False, None

    except Exception as e:
        return False, None

def process_album(client, media_info, download_folder, description, logger):
    media_pk = str(media_info.pk)
    try:
        resources = media_info.resources
        downloaded_paths = []
        for idx, resource in enumerate(resources):
            resource_pk = str(resource.pk)
            if resource.media_type == 1:
                media_url = resource.thumbnail_url
                extension = media_url.split('?')[0].split('.')[-1]
                downloaded_path = os.path.join(download_folder, f"{media_pk}_{idx}.{extension}")
                response = requests.get(media_url)
                with open(downloaded_path, 'wb') as f:
                    f.write(response.content)
                downloaded_paths.append(downloaded_path)
            elif resource.media_type == 2:
                media_url = resource.video_url
                downloaded_path = os.path.join(download_folder, f"{media_pk}_{idx}.mp4")

                ydl_opts = {
                    'outtmpl': downloaded_path,
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                    'quiet': False,
                    'no_warnings': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([media_url])

                if not os.path.isfile(downloaded_path):
                    continue

                downloaded_paths.append(downloaded_path)
            else:
                pass

        if not downloaded_paths:
            return False

        upload_success = uploadalbum(
            client,
            downloaded_paths,
            description
        )
        if upload_success:
            for path in downloaded_paths:
                os.remove(path)
            return True
        else:
            return False

    except Exception as e:
        return False

def randomdesc(description_file):
    with open(description_file, 'r', encoding='utf-8') as file:
        descriptions = json.load(file)
        random_key = random.choice(list(descriptions.keys()))
        description_list = descriptions[random_key]
        full_description = ''.join(description_list)
        return full_description
