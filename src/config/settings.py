import datetime
import logging

from src.db.models import Setting

logger = logging.getLogger(__name__)


class ConfigService:
    @staticmethod
    def get(key: str, default: str | None = None) -> str | None:
        try:
            row = Setting.get(Setting.key == key)
            return row.value
        except Setting.DoesNotExist:
            return default

    @staticmethod
    def set(key: str, value: str, is_encrypted: bool = False) -> None:
        now = datetime.datetime.now()
        Setting.insert(
            key=key, value=value, is_encrypted=is_encrypted, updated_at=now
        ).on_conflict_replace().execute()

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        val = ConfigService.get(key)
        if val is None:
            return default
        return val.lower() == "true"

    @staticmethod
    def set_bool(key: str, value: bool) -> None:
        ConfigService.set(key, "true" if value else "false")

    @staticmethod
    def is_onboarding_completed() -> bool:
        return ConfigService.get_bool("onboarding_completed", False)

    @staticmethod
    def mark_onboarding_completed() -> None:
        ConfigService.set_bool("onboarding_completed", True)

    @staticmethod
    def get_ai_config() -> dict:
        return {
            "provider": ConfigService.get("ai_provider"),
            "model": ConfigService.get("ai_model"),
            "endpoint": ConfigService.get("ai_endpoint"),
        }
