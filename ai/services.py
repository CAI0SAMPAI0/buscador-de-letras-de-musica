import json
import logging
from typing import List, Dict, Any, Optional
from .prompt_manager import PromptManager
from .providers import get_llm_provider

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.provider = get_llm_provider()

    async def expand_query(self, user_query: str) -> Dict[str, Any]:
        """
        Utiliza o prompt de expansão de consulta para obter variação/normalização inteligente do termo de busca.
        """
        system_prompt = PromptManager.get_prompt("system/system_prompt")
        user_prompt = PromptManager.get_prompt("search/query_expander", user_query=user_query)

        if not user_prompt:
            return {"normalized_query": user_query, "keywords": user_query.split()}

        raw_response = await self.provider.generate_completion(user_prompt, system_prompt=system_prompt)
        if not raw_response:
            return {"normalized_query": user_query, "keywords": user_query.split()}

        try:
            # Tenta encontrar bloco JSON na resposta
            start = raw_response.find("{")
            end = raw_response.rfind("}") + 1
            if start != -1 and end != -1:
                data = json.loads(raw_response[start:end])
                return data
        except Exception as e:
            logger.error(f"[AIService] Erro ao decodificar JSON de expansão de busca: {e}")

        return {"normalized_query": user_query, "keywords": user_query.split()}
