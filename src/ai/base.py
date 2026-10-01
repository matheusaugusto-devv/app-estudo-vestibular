from abc import ABC, abstractmethod


class IAIAdapter(ABC):
    @abstractmethod
    def test_connection(self) -> bool:
        pass

    @abstractmethod
    def extract(self, system_prompt: str, user_prompt: str, response_schema: dict) -> dict:
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        pass
