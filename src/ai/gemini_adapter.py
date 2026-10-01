import json
import logging

from src.ai.base import IAIAdapter
from src.ai.exceptions import AIAuthError, AIResponseError, AITimeoutError

logger = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 10
_EXTRACT_TIMEOUT = 60


class GeminiAdapter(IAIAdapter):
    MODELS = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"]

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model = model

    def _configure(self):
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        return genai

    def test_connection(self) -> bool:
        try:
            genai = self._configure()
            list(genai.list_models())
            return True
        except Exception as e:
            msg = str(e).lower()
            if "api key" in msg or "permission" in msg or "403" in msg:
                raise AIAuthError("Credenciais inválidas para Gemini.") from e
            raise

    def list_models(self) -> list[str]:
        try:
            genai = self._configure()
            models = genai.list_models()
            return [m.name.replace("models/", "") for m in models if "generateContent" in (m.supported_generation_methods or [])]
        except Exception as e:
            logger.warning("Failed to list Gemini models dynamically, returning defaults: %s", e)
            return self.MODELS

    def extract(self, system_prompt: str, user_prompt: str, response_schema: dict) -> dict:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            self.model,
            system_instruction=system_prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
            },
        )
        try:
            response = model.generate_content(user_prompt)
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise AIResponseError("Resposta inválida do LLM.") from e
