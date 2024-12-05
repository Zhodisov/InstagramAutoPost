import requests

def discord_webhook(title, description, color, webhook_url):
    data = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color
            }
        ]
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code != 204:
        pass