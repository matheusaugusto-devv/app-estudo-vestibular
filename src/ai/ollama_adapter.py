import json
import logging

import requests

from src.ai.base import IAIAdapter
from src.ai.exceptions import AIConnectionError, AIResponseError

logger = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 10
_EXTRACT_TIMEOUT = 60


class OllamaAdapter(IAIAdapter):
    def __init__(self, endpoint: str = "http://localhost:11434", model: str = ""):
        self.endpoint = endpoint.rstrip("/")
        self.model = model

    def test_connection(self) -> bool:
        try:
            resp = requests.get(f"{self.endpoint}/api/tags", timeout=_CONNECT_TIMEOUT)
            return resp.status_code == 200
        except requests.exceptions.ConnectionError as e:
            raise AIConnectionError("Não foi possível conectar ao Ollama.") from e
        except requests.exceptions.Timeout as e:
            raise AIConnectionError("Tempo limite excedido ao conectar ao Ollama.") from e

    def list_models(self) -> list[str]:
        try:
            resp = requests.get(f"{self.endpoint}/api/tags", timeout=_CONNECT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except requests.exceptions.ConnectionError as e:
            raise AIConnectionError("Não foi possível conectar ao Ollama.") from e

    def extract(self, system_prompt: str, user_prompt: str, response_schema: dict) -> dict:
        try:
            resp = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "format": response_schema,
                    "stream": False,
                },
                timeout=_EXTRACT_TIMEOUT,
            )
            resp.raise_for_status()
            content = resp.json().get("response", "")
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise AIResponseError("Resposta inválida do LLM.") from e
        except requests.exceptions.ConnectionError as e:
            raise AIConnectionError("Não foi possível conectar ao Ollama.") from e
