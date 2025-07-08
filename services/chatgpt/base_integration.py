from fastapi import HTTPException
from typing import Optional
import openai
from config import OPENAI_API_KEY

class BaseChatGPTIntegration:
    """
    Base asynchronous integrator for working with OpenAI ChatGPT.
    """
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or OPENAI_API_KEY
        if not key:
            raise HTTPException(status_code=500, detail="OpenAI API key not provided")
        self.async_client = openai.AsyncOpenAI(api_key=key)