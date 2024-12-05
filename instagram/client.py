import logging
import sys
import time
from instagrapi import Client
from instagrapi.exceptions import (
    ClientError, BadPassword, ReloginAttemptExceeded, ChallengeRequired,
    SelectContactPointRecoveryForm, RecaptchaChallengeForm,
    FeedbackRequired, PleaseWaitFewMinutes, LoginRequired
)
from utils.notifications import discord_webhook

class InstagramClient:
    def __init__(self, credentials, logger):
        self.credentials = credentials
        self.logger = logger
        self.client = self.load_instagram_session()

    def handle_exception(self, client, e):
        if isinstance(e, BadPassword):
            webhook_url = self.credentials.get("DISCORD_WEBHOOK_URL")
            if webhook_url:
                discord_webhook(
                    title="Ошибка подключения",
                    description="Пароль неверный",
                    color=15158332,  
                    webhook_url=webhook_url
                )
            sys.exit(1)
        elif isinstance(e, LoginRequired):
            client.relogin()
        elif isinstance(e, ChallengeRequired):
            self.handle_challenge(client, client.last_json)
        elif isinstance(e, FeedbackRequired):
            message = client.last_json.get("feedback_message", "")
            webhook_url = self.credentials.get("DISCORD_WEBHOOK_URL")
            if webhook_url:
                discord_webhook(
                    title="Требуется обратная связь",
                    description=f"Instagram прислал ответное сообщение : {message}",
                    color=15105570,  
                    webhook_url=webhook_url
                )
            time.sleep(600)
            # client.relogin()
        elif isinstance(e, PleaseWaitFewMinutes):
            webhook_url = self.credentials.get("DISCORD_WEBHOOK_URL")
            if webhook_url:
                discord_webhook(
                    title="Пожалуйста, подождите",
                    description="Instagram просит вас подождать несколько минут, прежде чем повторить попытку",
                    color=15105570,  
                    webhook_url=webhook_url
                )
            time.sleep(300)
            # client.relogin()
        elif isinstance(e, ReloginAttemptExceeded):
            webhook_url = self.credentials.get("DISCORD_WEBHOOK_URL")
            if webhook_url:
                discord_webhook(
                    title="Повторное подключение не удалось",
                    description="Превышено максимальное количество попыток повторного подключения",
                    color=15158332,  
                    webhook_url=webhook_url
                )
            sys.exit(1)
        else:
            webhook_url = self.credentials.get("DISCORD_WEBHOOK_URL")
            if webhook_url:
                discord_webhook(
                    title="Неизвестная ошибка",
                    description=f"Ошибка подключения : {e}",
                    color=15158332,  
                    webhook_url=webhook_url
                )
            sys.exit(1)

    def load_instagram_session(self):
        client = Client()
        proxy_url = self.credentials.get("PROXY_URL")
        if proxy_url:
            client.set_proxy(proxy_url)

        client.handle_exception = self.handle_exception

        try:
            client.login(self.credentials["INSTAGRAM_USERNAME"], self.credentials["INSTAGRAM_PASSWORD"])
            time.sleep(5)

            if client.last_json.get("challenge", False):
                self.handle_challenge(client, client.last_json)

            webhook_url = self.credentials.get("DISCORD_WEBHOOK_URL")
            if webhook_url:
                discord_webhook(
                    title="Успешное подключение",
                    description="Скрипт успешно подключился к Instagram",
                    color=3066993,  
                    webhook_url=webhook_url
                )
            return client

        except Exception as e:
            client.handle_exception(client, e)
            sys.exit(1)

    def handle_challenge(self, client, last_json):
        step_name = last_json.get("step_name", "")

        if step_name == "select_verify_method":
            choice = last_json.get("step_data", {}).get("choice")
            if choice:
                client.challenge_send_security_code(choice)
            else:
                client.challenge_resolve(last_json)
        elif step_name in ["verify_code", "delta_login_review"]:
            code = input("Введите код, полученный в Instagram: ")
            client.change_device()  
            result = client.challenge_code_send(code)
            if result:
                webhook_url = self.credentials.get("DISCORD_WEBHOOK_URL")
                if webhook_url:
                    discord_webhook(
                        title="Задача решена",
                        description="Задача Instagram успешно решена",
                        color=3066993,  
                        webhook_url=webhook_url
                    )
                return True
            else:
                webhook_url = self.credentials.get("DISCORD_WEBHOOK_URL")
                if webhook_url:
                    discord_webhook(
                        title="Вызов провален",
                        description="Код, предоставленный для решения задачи, неверен",
                        color=15158332,  
                        webhook_url=webhook_url
                    )
                sys.exit(1)
        else:
            webhook_url = self.credentials.get("DISCORD_WEBHOOK_URL")
            if webhook_url:
                discord_webhook(
                    title="Задача решается",
                    description=f"Обнаружена задача '{step_name}' Решите ее на своем телефоне",
                    color=15105570,  
                    webhook_url=webhook_url
                )
            while True:
                time.sleep(5)
                client.get_timeline_feed()
                if not client.last_json.get("challenge", False):
                    break
            return True

    def get_all_clips(self, username):
        try:
            user_id = self.client.user_id_from_username(username)

            amount_to_fetch = 1000
            clips = self.client.user_clips_v1(user_id, amount=amount_to_fetch)

            return clips
        except Exception as e:
            webhook_url = self.credentials.get("DISCORD_WEBHOOK_URL")
            if webhook_url:
                discord_webhook(
                    title="Ошибка при извлечении клипов",
                    description=f"Ошибка для @{username} : {e}",
                    color=15158332,
                    webhook_url=webhook_url
                )
            return []
