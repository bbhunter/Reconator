import logging
from typing import Optional, Protocol

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)


class Notifier(Protocol):
    enabled: bool

    def send(self, message: str) -> None: ...


class TelegramNotifier:
    def __init__(self, api_key: Optional[str], chat_id: Optional[str]) -> None:
        self.api_key = api_key
        self.chat_id = chat_id
        self._bot = None
        if api_key and chat_id:
            try:
                import telebot

                self._bot = telebot.TeleBot(api_key)
            except Exception as exc:  # noqa: BLE001
                log.warning("telegram init failed: %s", exc)
                self._bot = None
        self.enabled: bool = self._bot is not None

    def send(self, message: str) -> None:
        if not self.enabled:
            return
        try:
            self._bot.send_message(self.chat_id, message)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            log.warning("telegram send failed: %s", exc)


class WebhookNotifier:
    def __init__(self, url: Optional[str], kind: str = "generic") -> None:
        self.url = url
        self.kind = kind.lower()
        self.enabled: bool = bool(url)

    def _payload(self, message: str) -> dict:
        if self.kind == "slack":
            return {"text": message}
        if self.kind == "discord":
            return {"content": message}
        return {"message": message, "source": "reconator"}

    def send(self, message: str) -> None:
        if not self.enabled:
            return
        try:
            httpx.post(self.url, json=self._payload(message), timeout=10.0)  # type: ignore[arg-type]
        except Exception as exc:  # noqa: BLE001
            log.warning("webhook send failed kind=%s: %s", self.kind, exc)


class CompositeNotifier:
    def __init__(self, *notifiers: Notifier) -> None:
        self._notifiers = notifiers
        self.enabled: bool = any(n.enabled for n in notifiers)

    def send(self, message: str) -> None:
        for n in self._notifiers:
            if n.enabled:
                n.send(message)


telegram = TelegramNotifier(settings.telegram_api_key, settings.telegram_chat_id)
webhook = WebhookNotifier(settings.webhook_url, settings.webhook_kind)
notifier = CompositeNotifier(telegram, webhook)
