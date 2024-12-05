import json
import logging
import os

def ldownloaded(download_log_file):
    if os.path.exists(download_log_file):
        try:
            with open(download_log_file, 'r') as file:
                content = json.load(file)
                if isinstance(content, list):
                    return content
                else:
                    return []
        except json.JSONDecodeError as e:
            return []
    return []
def sdownloaded(downloaded_clips, download_log_file="logs/downloaded_clips.json"):
    with open(download_log_file, 'w') as file:
        json.dump(downloaded_clips, file, indent=4)
