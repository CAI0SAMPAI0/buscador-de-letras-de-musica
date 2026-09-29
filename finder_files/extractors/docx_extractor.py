import logging
from pathlib import Path
from typing import List
from docx import Document
from .base import BaseExtractor, ExtractedChunk

logger = logging.getLogger(__name__)

class DOCXExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> List[ExtractedChunk]:
        chunks: List[ExtractedChunk] = []
        try:
            doc = Document(str(file_path))
            paragraph_group = []
            
            for p in doc.paragraphs:
                text = p.text.strip()
                if text:
                    paragraph_group.append(text)
                    # Agrupa a cada ~4 parágrafos ou se for um cabeçalho
                    if len(paragraph_group) >= 4 or p.style.name.startswith('Heading'):
                        chunk_text = "\n".join(paragraph_group).strip()
                        chunks.append(
                            ExtractedChunk(
                                text=chunk_text,
                                page_number=None,
                                slide_number=None,
                                snippet=chunk_text[:250],
                                chunk_index=len(chunks)
                            )
                        )
                        paragraph_group = []
            
            if paragraph_group:
                chunk_text = "\n".join(paragraph_group).strip()
                chunks.append(
                    ExtractedChunk(
                        text=chunk_text,
                        page_number=None,
                        slide_number=None,
                        snippet=chunk_text[:250],
                        chunk_index=len(chunks)
                    )
                )
        except Exception as e:
            logger.error(f"Erro ao extrair texto do DOCX {file_path}: {e}")
        return chunks
