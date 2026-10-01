import base64
import hashlib
import logging

from src.config.settings import ConfigService

logger = logging.getLogger(__name__)

_KEYRING_SERVICE = "estudovest"
_KEYRING_KEY = "ai_api_key"
_ENC_MARKER = "enc::"


def _derive_key() -> bytes:
    import getpass
    user = getpass.getuser()
    return hashlib.sha256(user.encode()).digest()


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _encrypt(plaintext: str) -> str:
    key = _derive_key()
    enc = _xor(plaintext.encode(), key)
    return _ENC_MARKER + base64.b64encode(enc).decode()


def _decrypt(ciphertext: str) -> str:
    if not ciphertext.startswith(_ENC_MARKER):
        return ciphertext
    key = _derive_key()
    enc = base64.b64decode(ciphertext[len(_ENC_MARKER):])
    return _xor(enc, key).decode()


class CredentialService:
    @staticmethod
    def save_api_key(api_key: str) -> None:
        try:
            import keyring
            keyring.set_password(_KEYRING_SERVICE, _KEYRING_KEY, api_key)
            ConfigService.set("ai_api_key_stored", "keyring")
        except Exception as e:
            logger.warning("Failed to save credential to keyring: %s. Falling back to encrypted settings.", e)
            ConfigService.set("ai_api_key", _encrypt(api_key), is_encrypted=True)
            ConfigService.set("ai_api_key_stored", "settings")

    @staticmethod
    def get_api_key() -> str | None:
        stored = ConfigService.get("ai_api_key_stored")
        if stored == "keyring":
            try:
                import keyring
                return keyring.get_password(_KEYRING_SERVICE, _KEYRING_KEY)
            except Exception:
                pass
        val = ConfigService.get("ai_api_key")
        if val:
            return _decrypt(val)
        return None

    @staticmethod
    def clear_api_key() -> None:
        try:
            import keyring
            keyring.delete_password(_KEYRING_SERVICE, _KEYRING_KEY)
        except Exception:
            pass
        from src.db.models import Setting
        Setting.delete().where(Setting.key.in_(["ai_api_key", "ai_api_key_stored"])).execute()
