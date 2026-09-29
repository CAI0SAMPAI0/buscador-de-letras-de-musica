import logging
from typing import List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class BaseEmbeddingProvider:
    async def get_embedding(self, text: str) -> List[float]:
        raise NotImplementedError()


class DummyEmbeddingProvider(BaseEmbeddingProvider):
    async def get_embedding(self, text: str) -> List[float]:
        # Fallback determinístico caso nenhum serviço vetorial externo esteja configurado
        return [0.0] * 384


def get_embedding_provider() -> BaseEmbeddingProvider:
    return DummyEmbeddingProvider()
