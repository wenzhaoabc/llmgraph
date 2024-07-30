import os
from typing import Callable, Any
from openai import OpenAI


class LLM:
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
    ):
        self.api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")
        self.base_url = base_url if base_url else os.getenv("OPENAI_BASE_URL")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(
        self, messages: list, callback: Callable[[str], Any], model: str = "gpt-4o-mini"
    ) -> str:
        stream = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        content = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                if callback:
                    callback(chunk.choices[0].delta.content)
                content += chunk.choices[0].delta.content

        return content
