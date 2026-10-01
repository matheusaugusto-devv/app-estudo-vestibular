import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from src.db.connection import database, disconnect
from src.db import init_db


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    yield database
    disconnect()
    if not database.is_closed():
        database.close()


class TestConfigService:
    def test_get_returns_none_for_missing_key(self, db):
        from src.config.settings import ConfigService
        assert ConfigService.get("nonexistent") is None

    def test_get_returns_default_for_missing_key(self, db):
        from src.config.settings import ConfigService
        assert ConfigService.get("nonexistent", "fallback") == "fallback"

    def test_set_and_get(self, db):
        from src.config.settings import ConfigService
        ConfigService.set("ai_provider", "openai")
        assert ConfigService.get("ai_provider") == "openai"

    def test_set_overwrites_existing(self, db):
        from src.config.settings import ConfigService
        ConfigService.set("ai_provider", "openai")
        ConfigService.set("ai_provider", "gemini")
        assert ConfigService.get("ai_provider") == "gemini"

    def test_get_bool_and_set_bool(self, db):
        from src.config.settings import ConfigService
        ConfigService.set_bool("onboarding_completed", True)
        assert ConfigService.get_bool("onboarding_completed") is True
        ConfigService.set_bool("onboarding_completed", False)
        assert ConfigService.get_bool("onboarding_completed") is False

    def test_get_bool_default(self, db):
        from src.config.settings import ConfigService
        assert ConfigService.get_bool("missing", True) is True

    def test_is_onboarding_completed_false_by_default(self, db):
        from src.config.settings import ConfigService
        assert ConfigService.is_onboarding_completed() is False

    def test_mark_onboarding_completed(self, db):
        from src.config.settings import ConfigService
        ConfigService.mark_onboarding_completed()
        assert ConfigService.is_onboarding_completed() is True

    def test_get_ai_config(self, db):
        from src.config.settings import ConfigService
        ConfigService.set("ai_provider", "openai")
        ConfigService.set("ai_model", "gpt-4o")
        ConfigService.set("ai_endpoint", "http://localhost:11434")
        config = ConfigService.get_ai_config()
        assert config["provider"] == "openai"
        assert config["model"] == "gpt-4o"
        assert config["endpoint"] == "http://localhost:11434"


class TestCredentialService:
    def test_save_and_get_via_keyring(self, db):
        from src.config.credentials import CredentialService
        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = "sk-secret"
        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            CredentialService.save_api_key("sk-secret")
            result = CredentialService.get_api_key()
        assert result == "sk-secret"

    def test_fallback_to_encrypted_settings(self, db):
        from src.config.credentials import CredentialService
        with patch.dict("sys.modules", {"keyring": None}):
            import builtins
            real_import = builtins.__import__
            def _fake_import(name, *args, **kwargs):
                if name == "keyring":
                    raise ImportError("no keyring")
                return real_import(name, *args, **kwargs)
            with patch("builtins.__import__", side_effect=_fake_import):
                CredentialService.save_api_key("sk-secret-fallback")
                result = CredentialService.get_api_key()
        assert result == "sk-secret-fallback"

    def test_clear_api_key(self, db):
        from src.config.credentials import CredentialService
        mock_keyring = MagicMock()
        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            CredentialService.save_api_key("sk-secret")
            CredentialService.clear_api_key()
            result = CredentialService.get_api_key()
        assert result is None


class TestAIExceptions:
    def test_exception_hierarchy(self):
        from src.ai.exceptions import (
            AIException, AIAuthError, AIRateLimitError, AITimeoutError,
            AIResponseError, AIConnectionError, AINotConfiguredError, AIModelError,
        )
        for exc_cls in [AIAuthError, AIRateLimitError, AITimeoutError, AIResponseError, AIConnectionError, AINotConfiguredError, AIModelError]:
            assert issubclass(exc_cls, AIException)

    def test_auth_error_message(self):
        from src.ai.exceptions import AIAuthError
        e = AIAuthError("Credenciais inválidas para OpenAI.")
        assert "Credenciais" in str(e)


class TestIAIAdapter:
    def test_cannot_instantiate_abc(self):
        from src.ai.base import IAIAdapter
        with pytest.raises(TypeError):
            IAIAdapter()

    def test_has_three_abstract_methods(self):
        from src.ai.base import IAIAdapter
        abstract_methods = IAIAdapter.__abstractmethods__
        assert "test_connection" in abstract_methods
        assert "extract" in abstract_methods
        assert "list_models" in abstract_methods


class TestOllamaAdapter:
    def test_list_models_success(self):
        from src.ai.ollama_adapter import OllamaAdapter
        adapter = OllamaAdapter(endpoint="http://localhost:11434")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "llama3"}, {"name": "mistral"}]}
        mock_resp.raise_for_status = MagicMock()
        with patch("src.ai.ollama_adapter.requests.get", return_value=mock_resp):
            models = adapter.list_models()
        assert models == ["llama3", "mistral"]

    def test_test_connection_success(self):
        from src.ai.ollama_adapter import OllamaAdapter
        adapter = OllamaAdapter(endpoint="http://localhost:11434")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("src.ai.ollama_adapter.requests.get", return_value=mock_resp):
            assert adapter.test_connection() is True

    def test_test_connection_failure_raises(self):
        from src.ai.ollama_adapter import OllamaAdapter
        from src.ai.exceptions import AIConnectionError
        import requests as req
        adapter = OllamaAdapter(endpoint="http://localhost:11434")
        with patch("src.ai.ollama_adapter.requests.get", side_effect=req.exceptions.ConnectionError()):
            with pytest.raises(AIConnectionError):
                adapter.test_connection()


class TestOpenAIAdapter:
    def test_list_models_success(self):
        from src.ai.openai_adapter import OpenAIAdapter
        adapter = OpenAIAdapter(api_key="sk-test")
        mock_client = MagicMock()
        mock_model_1 = MagicMock()
        mock_model_1.id = "gpt-4o"
        mock_model_2 = MagicMock()
        mock_model_2.id = "gpt-4o-mini"
        mock_client.models.list.return_value.data = [mock_model_1, mock_model_2]
        with patch.object(adapter, "_get_client", return_value=mock_client):
            models = adapter.list_models()
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models

    def test_test_connection_success(self):
        from src.ai.openai_adapter import OpenAIAdapter
        adapter = OpenAIAdapter(api_key="sk-test")
        mock_client = MagicMock()
        mock_client.models.list.return_value.data = []
        with patch.object(adapter, "_get_client", return_value=mock_client):
            assert adapter.test_connection() is True

    def test_test_connection_auth_error(self):
        from src.ai.openai_adapter import OpenAIAdapter
        from src.ai.exceptions import AIAuthError
        adapter = OpenAIAdapter(api_key="sk-invalid")
        mock_client = MagicMock()
        error = Exception("Unauthorized")
        error.status_code = 401
        mock_client.models.list.side_effect = error
        with patch.object(adapter, "_get_client", return_value=mock_client):
            with pytest.raises(AIAuthError):
                adapter.test_connection()


class TestClaudeAdapter:
    def test_list_models_hardcoded(self):
        from src.ai.claude_adapter import ClaudeAdapter
        adapter = ClaudeAdapter(api_key="sk-test")
        models = adapter.list_models()
        assert "claude-3.5-sonnet" in models
        assert "claude-3-haiku" not in models or "claude-3.5-haiku" in models


class TestGeminiAdapter:
    def test_list_models_success(self):
        from src.ai.gemini_adapter import GeminiAdapter
        adapter = GeminiAdapter(api_key="test-key")
        mock_genai = MagicMock()
        mock_m1 = MagicMock()
        mock_m1.name = "models/gemini-1.5-pro"
        mock_m1.supported_generation_methods = ["generateContent"]
        mock_m2 = MagicMock()
        mock_m2.name = "models/gemini-1.5-flash"
        mock_m2.supported_generation_methods = ["generateContent"]
        mock_genai.list_models.return_value = [mock_m1, mock_m2]
        with patch.object(adapter, "_configure", return_value=mock_genai):
            models = adapter.list_models()
        assert "gemini-1.5-pro" in models
        assert "gemini-1.5-flash" in models


class TestAIProviderService:
    def test_get_adapter_openai(self, db):
        from src.ai.provider_service import AIProviderService
        from src.ai.openai_adapter import OpenAIAdapter
        from src.config.settings import ConfigService
        from src.config.credentials import CredentialService
        ConfigService.set("ai_provider", "openai")
        ConfigService.set("ai_model", "gpt-4o")
        with patch.object(CredentialService, "get_api_key", return_value="sk-test"):
            adapter = AIProviderService.get_adapter()
        assert isinstance(adapter, OpenAIAdapter)

    def test_get_adapter_ollama(self, db):
        from src.ai.provider_service import AIProviderService
        from src.ai.ollama_adapter import OllamaAdapter
        from src.config.settings import ConfigService
        ConfigService.set("ai_provider", "ollama")
        ConfigService.set("ai_model", "llama3")
        ConfigService.set("ai_endpoint", "http://localhost:11434")
        adapter = AIProviderService.get_adapter()
        assert isinstance(adapter, OllamaAdapter)

    def test_get_adapter_not_configured(self, db):
        from src.ai.provider_service import AIProviderService
        from src.ai.exceptions import AINotConfiguredError
        with pytest.raises(AINotConfiguredError):
            AIProviderService.get_adapter()

    def test_test_provider_ollama(self):
        from src.ai.provider_service import AIProviderService
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("src.ai.ollama_adapter.requests.get", return_value=mock_resp):
            assert AIProviderService.test_provider("ollama", endpoint="http://localhost:11434") is True

    def test_list_models_for_claude(self):
        from src.ai.provider_service import AIProviderService
        models = AIProviderService.list_models_for("claude", api_key="fake")
        assert "claude-3.5-sonnet" in models


class TestOnboardingDetection:
    def test_onboarding_shown_when_not_completed(self, db):
        from src.config.settings import ConfigService
        assert not ConfigService.is_onboarding_completed()

    def test_onboarding_not_shown_after_completion(self, db):
        from src.config.settings import ConfigService
        ConfigService.mark_onboarding_completed()
        assert ConfigService.is_onboarding_completed()

    def test_onboarding_persists_provider_and_model(self, db):
        from src.config.settings import ConfigService
        ConfigService.set("ai_provider", "openai")
        ConfigService.set("ai_model", "gpt-4o")
        ConfigService.mark_onboarding_completed()
        assert ConfigService.get("ai_provider") == "openai"
        assert ConfigService.get("ai_model") == "gpt-4o"
        assert ConfigService.is_onboarding_completed()
