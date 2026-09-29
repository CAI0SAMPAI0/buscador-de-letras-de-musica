import logging
import re
from pathlib import Path
from typing import List
from .base import BaseExtractor, ExtractedChunk

logger = logging.getLogger(__name__)

class DOCExtractor(BaseExtractor):
    """
    Extrator de arquivos Word legados (.doc).
    Tenta utilitário MS Word win32com se disponível no Windows,
    ou fallback por extração textual binária de streams olefile/ASCII.
    """
    def extract(self, file_path: Path) -> List[ExtractedChunk]:
        chunks: List[ExtractedChunk] = []

        # Tentativa 1: win32com MS Word no Windows
        try:
            import win32com.client
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass

            word_app = win32com.client.DispatchEx("Word.Application")
            word_app.Visible = False
            try:
                doc = word_app.Documents.Open(str(file_path), ReadOnly=True)
                full_text = doc.Content.Text
                doc.Close(False)

                paragraphs = [p.strip() for p in full_text.splitlines() if p.strip()]
                for i in range(0, len(paragraphs), 4):
                    group = "\n".join(paragraphs[i:i+4])
                    chunks.append(
                        ExtractedChunk(
                            text=group,
                            page_number=None,
                            slide_number=None,
                            snippet=group[:250],
                            chunk_index=len(chunks)
                        )
                    )
                return chunks
            finally:
                try:
                    word_app.Quit()
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"win32com fallback ativado para DOC {file_path}: {e}")

        # Tentativa 2: Extração de texto de stream binário
        try:
            with open(file_path, "rb") as f:
                content = f.read()

            text_blocks = re.findall(b'[\x20-\x7E\x0A\x0D\x09]{4,}', content)
            raw_text = "\n".join([b.decode('latin1', errors='ignore') for b in text_blocks])

            lines = [l.strip() for l in raw_text.splitlines() if len(l.strip()) > 3]
            for i in range(0, len(lines), 5):
                group = "\n".join(lines[i:i+5])
                chunks.append(
                    ExtractedChunk(
                        text=group,
                        page_number=None,
                        slide_number=None,
                        snippet=group[:250],
                        chunk_index=len(chunks)
                    )
                )
        except Exception as e:
            logger.error(f"Erro ao extrair texto binário de DOC {file_path}: {e}")

        return chunks
