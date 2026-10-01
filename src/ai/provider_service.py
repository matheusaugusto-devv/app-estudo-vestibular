from src.ai.base import IAIAdapter
from src.ai.exceptions import AINotConfiguredError
from src.ai.openai_adapter import OpenAIAdapter
from src.ai.gemini_adapter import GeminiAdapter
from src.ai.claude_adapter import ClaudeAdapter
from src.ai.ollama_adapter import OllamaAdapter
from src.config.credentials import CredentialService
from src.config.settings import ConfigService


class AIProviderService:
    @staticmethod
    def get_adapter() -> IAIAdapter:
        provider = ConfigService.get("ai_provider")
        model = ConfigService.get("ai_model") or ""
        endpoint = ConfigService.get("ai_endpoint") or "http://localhost:11434"
        api_key = CredentialService.get_api_key() or ""

        if provider is None:
            raise AINotConfiguredError("Configure a IA nas Configurações.")

        if provider == "openai":
            return OpenAIAdapter(api_key=api_key, model=model)
        elif provider == "gemini":
            return GeminiAdapter(api_key=api_key, model=model)
        elif provider == "claude":
            return ClaudeAdapter(api_key=api_key, model=model)
        elif provider == "ollama":
            return OllamaAdapter(endpoint=endpoint, model=model)
        else:
            raise AINotConfiguredError(f"Provedor não suportado: {provider}")

    @staticmethod
    def test_provider(provider: str, api_key: str = "", endpoint: str = "", model: str = "") -> bool:
        if provider == "openai":
            return OpenAIAdapter(api_key=api_key, model=model or "gpt-4o").test_connection()
        elif provider == "gemini":
            return GeminiAdapter(api_key=api_key, model=model or "gemini-1.5-pro").test_connection()
        elif provider == "claude":
            return ClaudeAdapter(api_key=api_key, model=model or "claude-3.5-sonnet").test_connection()
        elif provider == "ollama":
            return OllamaAdapter(endpoint=endpoint or "http://localhost:11434", model=model).test_connection()
        else:
            raise ValueError(f"Provedor não suportado: {provider}")

    @staticmethod
    def list_models_for(provider: str, api_key: str = "", endpoint: str = "") -> list[str]:
        if provider == "openai":
            return OpenAIAdapter(api_key=api_key).list_models()
        elif provider == "gemini":
            return GeminiAdapter(api_key=api_key).list_models()
        elif provider == "claude":
            return ClaudeAdapter(api_key=api_key).list_models()
        elif provider == "ollama":
            return OllamaAdapter(endpoint=endpoint or "http://localhost:11434").list_models()
        else:
            return []
