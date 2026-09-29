import os
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class BaseLLMProvider:
    async def generate_completion(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        raise NotImplementedError()


class MetaLlamaProvider(BaseLLMProvider):
    """
    Provedor Meta Llama acessado via endpoint compatível com OpenAI (Novita AI, Groq, etc.).
    """
    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or getattr(settings, "LLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct:novita")
        self.api_key = api_key or getattr(settings, "LLM_API_KEY", "") or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or getattr(settings, "LLM_BASE_URL", "https://api.novita.ai/v3/openai")

    async def generate_completion(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            logger.warning("[MetaLlamaProvider] LLM_API_KEY não configurada. Retornando resposta padrão sem chamada remota.")
            return ""

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=1000
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"[MetaLlamaProvider] Erro ao chamar LLM ({self.model}): {e}")
            return ""


def get_llm_provider() -> BaseLLMProvider:
    provider_name = getattr(settings, "LLM_PROVIDER", "meta_llama").lower()
    if provider_name in ("meta_llama", "llama", "novita", "groq", "openai"):
        return MetaLlamaProvider()
    return MetaLlamaProvider()
