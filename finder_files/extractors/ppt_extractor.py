import logging
import re
import struct
from pathlib import Path
from typing import List, Optional
import olefile
from .base import BaseExtractor, ExtractedChunk

logger = logging.getLogger(__name__)


def sanitize_presentation_text(text: str) -> str:
    """
    Remove caracteres de controle, bytes binários corrompidos e ruídos de metadados,
    preservando caracteres acentuados da língua portuguesa.
    """
    if not text:
        return ""

    # Preserva quebras de linha e caracteres visíveis/acentuados
    cleaned_chars = []
    for ch in text:
        code = ord(ch)
        if ch in ('\n', '\r', '\t'):
            cleaned_chars.append('\n')
        elif code >= 32 and (ch.isprintable() or ch.isalnum()):
            cleaned_chars.append(ch)

    cleaned = "".join(cleaned_chars)

    noise_tokens = {
        'fontes usadas', 'tulos de slides', 'clique para editar', 'click to add',
        '[content_types]', '_rels', 'shapexml', 'downrev', '.rels', '.xml', 'drs/',
        'slide layout', 'slide master'
    }

    clean_lines = []
    for raw_l in cleaned.splitlines():
        l = raw_l.strip(" \t\r-–.,;:")
        if len(l) < 3:
            continue
        
        # Elimina linhas com menos de 45% de letras/números (resquícios de lixo binário)
        alnum_count = sum(1 for c in l if c.isalnum())
        if alnum_count / len(l) < 0.45:
            continue

        lower = l.lower()
        if any(nt in lower for nt in noise_tokens):
            continue

        # Evita duplicatas consecutivas idênticas
        if not clean_lines or clean_lines[-1] != l:
            clean_lines.append(l)

    return "\n".join(clean_lines)


class PPTExtractor(BaseExtractor):
    """
    Extrator robusto de arquivos legados de apresentações (.ppt).
    Identifica arquivos PPTX renomeados, utiliza OLE stream parsing estruturado
    para extrair slides reais e limpa caracteres binários corrompidos.
    """

    def extract(self, file_path: Path) -> List[ExtractedChunk]:
        chunks: List[ExtractedChunk] = []
        if not file_path.exists() or file_path.stat().st_size == 0:
            return chunks

        # 1. Se o arquivo for na verdade um PPTX compactado (PK\x03\x04), usa o PPTXExtractor diretamente
        try:
            with open(file_path, "rb") as f:
                head = f.read(16)
            if head.startswith(b"PK\x03\x04"):
                from .pptx_extractor import PPTXExtractor
                logger.info(f"Arquivo .ppt identificado como formato PPTX: {file_path.name}")
                return PPTXExtractor().extract(file_path)
        except Exception as e:
            logger.debug(f"Verificação de cabeçalho PPTX falhou: {e}")

        # 2. Tentativa via OLE2 estruturado (PowerPoint Document stream)
        try:
            if olefile.isOleFile(str(file_path)):
                with olefile.OleFileIO(str(file_path)) as ole:
                    if ole.exists('PowerPoint Document'):
                        stream = ole.openstream('PowerPoint Document').read()
                        chunks = self._extract_from_ppt_stream(stream)
                        if chunks:
                            return chunks
        except Exception as ole_err:
            logger.debug(f"OLE stream parsing falhou em {file_path.name}: {ole_err}")

        # 3. Tentativa via win32com no Windows (se PowerPoint instalado)
        try:
            import win32com.client
            pythoncom = None
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass

            ppt_app = win32com.client.DispatchEx("PowerPoint.Application")
            try:
                presentation = ppt_app.Presentations.Open(str(file_path), WithWindow=False)
                for slide_idx in range(1, presentation.Slides.Count + 1):
                    slide = presentation.Slides(slide_idx)
                    slide_texts = []
                    for shape in slide.Shapes:
                        if shape.HasTextFrame and shape.TextFrame.HasText:
                            slide_texts.append(shape.TextFrame.TextRange.Text.strip())
                    clean = sanitize_presentation_text("\n".join(slide_texts))
                    if clean:
                        chunks.append(
                            ExtractedChunk(
                                text=clean,
                                page_number=None,
                                slide_number=slide_idx,
                                snippet=clean[:250],
                                chunk_index=len(chunks)
                            )
                        )
                presentation.Close()
                if chunks:
                    return chunks
            finally:
                try:
                    ppt_app.Quit()
                except Exception:
                    pass
        except Exception:
            pass

        return chunks

    def _extract_from_ppt_stream(self, stream: bytes) -> List[ExtractedChunk]:
        """
        Analisa os registros binários do PowerPoint Document stream:
        Record 1006 (0x03EE) -> Slide Container (delimita o número do slide real)
        Record 4000 (0x0FA0) -> TextCharsAtom (UTF-16LE)
        Record 4008 (0x0FA8) -> TextBytesAtom (Latin-1 / ANSI)
        """
        chunks: List[ExtractedChunk] = []
        offset = 0
        stream_len = len(stream)

        slides_data: List[List[str]] = []
        current_slide_texts: List[str] = []

        while offset + 8 <= stream_len:
            ver_inst, rec_type, rec_len = struct.unpack('<HHI', stream[offset:offset+8])
            offset += 8
            if offset + rec_len > stream_len:
                break

            # 1006 = Slide Container: delimita novo slide
            if rec_type == 1006:
                if current_slide_texts:
                    slides_data.append(current_slide_texts)
                    current_slide_texts = []
            elif rec_type == 4000:  # UTF-16LE text
                try:
                    raw = stream[offset:offset+rec_len].decode('utf-16le', errors='ignore')
                    txt = sanitize_presentation_text(raw)
                    if txt:
                        current_slide_texts.append(txt)
                except Exception:
                    pass
            elif rec_type == 4008:  # Latin1 / ANSI text
                try:
                    raw = stream[offset:offset+rec_len].decode('latin1', errors='ignore')
                    txt = sanitize_presentation_text(raw)
                    if txt:
                        current_slide_texts.append(txt)
                except Exception:
                    pass

            # Registros do tipo container têm os 4 bits inferiores de ver_inst como 0x0F
            is_container = (ver_inst & 0x0F) == 0x0F
            if not is_container:
                offset += rec_len

        if current_slide_texts:
            slides_data.append(current_slide_texts)

        # Monta os chunks com numeração de slide real (1, 2, 3...)
        slide_num = 1
        for slide_items in slides_data:
            combined = sanitize_presentation_text("\n".join(slide_items))
            if combined and len(combined) >= 4:
                chunks.append(
                    ExtractedChunk(
                        text=combined,
                        page_number=None,
                        slide_number=slide_num,
                        snippet=combined[:250],
                        chunk_index=len(chunks)
                    )
                )
            slide_num += 1

        return chunks
