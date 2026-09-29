import os
import re
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Gerenciador centralizado de Prompts do Buscador de Músicas.
    Carrega prompts versionados em arquivos Markdown (.md) em ai/prompts/.
    Suporta cache em memória, recarregamento automático por mtime e interpolação segura.
    """

    _CACHE: Dict[str, str] = {}
    _MTIMES: Dict[str, float] = {}

    @classmethod
    def get_prompts_dir(cls) -> str:
        base_dir = getattr(settings, "BASE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_dir, "ai", "prompts")

    @classmethod
    def load_raw_prompt(cls, prompt_path: str, force_reload: bool = False) -> str:
        """
        Carrega o conteúdo cru do arquivo .md correspondente (ex: 'system/system_prompt' ou 'search/query_expander').
        """
        rel_path = prompt_path if prompt_path.endswith(".md") else f"{prompt_path}.md"
        filepath = os.path.join(cls.get_prompts_dir(), rel_path)

        if not os.path.exists(filepath):
            logger.warning(f"[PromptManager] Arquivo de prompt não encontrado: {filepath}")
            return ""

        try:
            mtime = os.path.getmtime(filepath)
            if not force_reload and prompt_path in cls._CACHE and cls._MTIMES.get(prompt_path) == mtime:
                return cls._CACHE[prompt_path]

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            cls._CACHE[prompt_path] = content
            cls._MTIMES[prompt_path] = mtime
            return content
        except Exception as e:
            logger.error(f"[PromptManager] Erro ao ler prompt '{prompt_path}' de {filepath}: {e}")
            return cls._CACHE.get(prompt_path, "")

    @classmethod
    def get_prompt(
        cls,
        prompt_path: str,
        section: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        content = cls.load_raw_prompt(prompt_path)
        if not content:
            return ""

        text = content
        if section:
            pattern = rf"##\s+{re.escape(section)}\s*\n(?:```(?:[a-zA-Z0-9_-]+)?\n)?(.*?)(?:```|\n##|\Z)"
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1).strip()

        # Interpolação de variáveis ({chave}) sem corromper estruturas JSON literais
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            text = text.replace(placeholder, str(value) if value is not None else "")

        return text.strip()

    @classmethod
    def clear_cache(cls):
        cls._CACHE.clear()
        cls._MTIMES.clear()
