import logging
from pathlib import Path
from typing import List
from pypdf import PdfReader
from .base import BaseExtractor, ExtractedChunk

logger = logging.getLogger(__name__)

class PDFExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> List[ExtractedChunk]:
        chunks: List[ExtractedChunk] = []
        try:
            reader = PdfReader(str(file_path))
            for page_idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                cleaned_text = text.strip()
                if cleaned_text:
                    # Divisão por parágrafos para múltiplos chunks se a página for longa
                    paragraphs = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]
                    if not paragraphs:
                        paragraphs = [cleaned_text]
                    
                    for chunk_i, para in enumerate(paragraphs):
                        chunks.append(
                            ExtractedChunk(
                                text=para,
                                page_number=page_idx,
                                slide_number=None,
                                snippet=para[:250],
                                chunk_index=len(chunks)
                            )
                        )
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF {file_path}: {e}")
        return chunks
