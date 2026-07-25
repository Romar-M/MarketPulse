import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

import asyncio
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class TelegramBot:
    """Отправляет сообщения в Telegram через Bot API."""

    def __init__(self, token: str, chat_id: Optional[str] = None):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{token}"

    async def send_message(self, text: str, chat_id: Optional[str] = None) -> bool:
        """Отправить сообщение в Telegram."""
        cid = chat_id or self.chat_id
        if not cid:
            logger.warning("chat_id не указан, сообщение не отправлено")
            return False

        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": cid,
            "text": text,
            "parse_mode": "HTML",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                logger.info("Сообщение отправлено в чат %s", cid)
                return True
        except Exception as e:
            logger.error("Ошибка отправки в Telegram: %s", e)
            return False

    async def get_updates(self) -> list[dict]:
        """Получить последние обновления (чтобы узнать chat_id)."""
        url = f"{self.api_url}/getUpdates"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                return data.get("result", [])
        except Exception as e:
            logger.error("Ошибка получения обновлений: %s", e)
            return []

    @staticmethod
    def extract_chat_id(updates: list[dict]) -> Optional[str]:
        """Извлечь chat_id из первого сообщения."""
        for upd in updates:
            msg = upd.get("message", {})
            chat = msg.get("chat", {})
            if chat.get("id"):
                return str(chat["id"])
        return None
