import logging
from typing import Optional

from app.core.config import settings

log = logging.getLogger(__name__)


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
                log.warning("telegram bot init failed: %s", exc)
                self._bot = None

    @property
    def enabled(self) -> bool:
        return self._bot is not None

    def send(self, message: str) -> None:
        if not self.enabled:
            log.info("notifier disabled — skipping: %s", message)
            return
        try:
            self._bot.send_message(self.chat_id, message)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            log.warning("telegram send failed: %s", exc)


notifier = TelegramNotifier(settings.telegram_api_key, settings.telegram_chat_id)
