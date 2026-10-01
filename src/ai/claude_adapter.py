import json
import logging

from src.ai.base import IAIAdapter
from src.ai.exceptions import AIAuthError, AIResponseError

logger = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 10
_EXTRACT_TIMEOUT = 60


class ClaudeAdapter(IAIAdapter):
    MODELS = ["claude-3.5-sonnet", "claude-3.5-haiku", "claude-3-opus"]

    def __init__(self, api_key: str, model: str = "claude-3.5-sonnet"):
        self.api_key = api_key
        self.model = model

    def _get_client(self):
        from anthropic import Anthropic
        return Anthropic(api_key=self.api_key, timeout=_CONNECT_TIMEOUT)

    def test_connection(self) -> bool:
        try:
            client = self._get_client()
            client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status in (401, 403):
                raise AIAuthError("Credenciais inválidas para Claude.") from e
            raise

    def list_models(self) -> list[str]:
        return self.MODELS

    def extract(self, system_prompt: str, user_prompt: str, response_schema: dict) -> dict:
        from anthropic import Anthropic
        client = Anthropic(api_key=self.api_key, timeout=_EXTRACT_TIMEOUT)
        schema_str = json.dumps(response_schema, indent=2)
        full_prompt = f"{user_prompt}\n\nRetorne APENAS JSON válido conforme este schema:\n{schema_str}"
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": full_prompt}],
            )
            content = response.content[0].text
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise AIResponseError("Resposta inválida do LLM.") from e
