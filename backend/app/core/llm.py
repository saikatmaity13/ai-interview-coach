import os
import json
from openai import OpenAI
from pydantic import BaseModel
from typing import TypeVar, Type, Union

from dotenv import load_dotenv

load_dotenv()

T = TypeVar('T', bound=BaseModel)

class GrokClient:
    def __init__(self):
        api_key = os.environ.get("GROK_API_KEY") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("No API key found! Please set GROK_API_KEY or GROQ_API_KEY in .env file.")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model_name = "llama-3.3-70b-versatile"

    def generate_content(self, prompt: str, response_schema: Type[T] = None) -> Union[str, T]:
        if response_schema:
            # Embed the JSON schema in the prompt and use json_object mode
            schema_str = json.dumps(response_schema.model_json_schema(), indent=2)
            full_prompt = (
                f"{prompt}\n\n"
                f"You MUST respond with a valid JSON object that exactly matches this schema:\n"
                f"{schema_str}\n"
                f"Return ONLY the JSON object, no extra text."
            )
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": full_prompt}],
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content
            return response_schema.model_validate_json(raw)
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

llm_client = GrokClient()

