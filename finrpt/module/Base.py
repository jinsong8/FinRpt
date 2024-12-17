from abc import ABC, abstractmethod
from finrpt.module.OpenAI import OpenAIModel


class BaseModel(ABC):
    def __init__(self, max_rounds=3, model_name='gpt-4o', language="zh"):
        self.system_prompt = "You are a helpful assistant that answers questions based on the context provided."
        self.max_rounds = max_rounds
        self.model = OpenAIModel(model_name=model_name, max_rounds=3)
        self.language = language

    @abstractmethod
    def run(self, data):
        raise NotImplementedError

