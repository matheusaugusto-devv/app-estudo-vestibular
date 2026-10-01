import json
import logging
import time

from src.ai.base import IAIAdapter
from src.ai.exceptions import AIAuthError, AIRateLimitError, AITimeoutError, AIResponseError

logger = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 10
_EXTRACT_TIMEOUT = 60
_MAX_RETRIES = 3


def _retry_on_rate_limit(fn, *args, **kwargs):
    for attempt in range(_MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status == 429 and attempt < _MAX_RETRIES - 1:
                delay = 2 ** attempt
                logger.warning("Rate limited, retrying in %ss", delay)
                time.sleep(delay)
                continue
            if status in (401, 403):
                raise AIAuthError(f"Credenciais inválidas para OpenAI.") from e
            raise
    raise AIRateLimitError("Rate limit excedido após 3 tentativas.")


class OpenAIAdapter(IAIAdapter):
    MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    def _get_client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, timeout=_CONNECT_TIMEOUT)

    def test_connection(self) -> bool:
        try:
            client = self._get_client()
            client.models.list()
            return True
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status in (401, 403):
                raise AIAuthError("Credenciais inválidas para OpenAI.") from e
            raise

    def list_models(self) -> list[str]:
        try:
            client = self._get_client()
            response = client.models.list()
            return [m.id for m in response.data]
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status in (401, 403):
                raise AIAuthError("Credenciais inválidas para OpenAI.") from e
            logger.warning("Failed to list models dynamically, returning defaults: %s", e)
            return self.MODELS

    def extract(self, system_prompt: str, user_prompt: str, response_schema: dict) -> dict:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, timeout=_EXTRACT_TIMEOUT)

        def _call():
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_schema", "json_schema": {"name": "response", "schema": response_schema, "strict": True}},
            )
            content = response.choices[0].message.content
            return json.loads(content)

        try:
            return _retry_on_rate_limit(_call)
        except json.JSONDecodeError as e:
            raise AIResponseError("Resposta inválida do LLM.") from e
