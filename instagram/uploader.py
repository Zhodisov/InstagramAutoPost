import logging
import time

from instagrapi.types import StoryLink, Track
from instagrapi.story import StoryBuilder
from instagrapi import Client

def clipcount(client, user_id):
    user_clips = client.user_clips_v1(user_id)
    return len(user_clips)

def cliplocation(client, downloaded_clip_path, description):
    try:
        client.clip_upload(
            downloaded_clip_path,
            description,
            extra_data={"like_and_view_counts_disabled": 1}
        )
        time.sleep(17)
        return True
    except Exception as e:
        return False

def clipmusic(client, video_path, description, track):
    try:
        client.clip_upload_as_reel_with_music(
            video_path,
            caption=description,
            track=track,
            extra_data={"like_and_view_counts_disabled": 1}
        )
        time.sleep(17)
        return True
    except Exception as e:
        return False

def uploadphoto(client, photo_path, description):
    try:
        client.photo_upload(
            photo_path,
            caption=description,
            extra_data={"like_and_view_counts_disabled": 1}
        )
        time.sleep(17)
        return True
    except Exception as e:
        return False

def uploadalbum(client, media_paths, description):
    try:
        client.album_upload(
            media_paths,
            caption=description,
            extra_data={"like_and_view_counts_disabled": 1}
        )
        time.sleep(17)
        return True
    except Exception as e:
        return False

def clipstory(client, clip_path, original_username, media_pk):
    try:
        link = StoryLink(
            webUri='https://www.instagram.com/tserlmkt974/',
            x=0.587,
            y=0.847,
            width=0.313,
            height=0.097,
            rotation=0.0
        )

        client.video_upload_to_story(
            clip_path,
            "👉 Follow for more 🔥 @tserlmkt974",
            links=[link]
        )

        time.sleep(6)
        return True
    except Exception as e:
        return False

def noteuploader(client, uploaded_count):
    note_text = f"📢 {uploaded_count}"
    try:
        client.notes_create(note_text, audience='0')
    except Exception as e:
        pass