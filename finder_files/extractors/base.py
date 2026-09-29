from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path
import unicodedata

@dataclass
class ExtractedChunk:
    text: str
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    snippet: str = ""
    chunk_index: int = 0

    def __post_init__(self):
        if not self.snippet:
            self.snippet = self.text[:250].strip()

def normalize_text(text: str) -> str:
    """Normaliza o texto removendo acentos, espaços nas pontas e convertendo para minúsculas."""
    if not text:
        return ""
    text = text.strip()
    nfkd_form = unicodedata.normalize('NFKD', text)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return only_ascii.lower()


class BaseExtractor:
    def extract(self, file_path: Path) -> List[ExtractedChunk]:
        raise NotImplementedError("Subclasses devem implementar extract()")
