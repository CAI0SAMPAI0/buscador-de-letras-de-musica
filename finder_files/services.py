import os
import re
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from asgiref.sync import sync_to_async
from django.db import transaction, connection
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.core.management import call_command

from .models import IndexedFile, DocumentChunk
from .extractors import (
    PDFExtractor,
    PPTXExtractor,
    PPTExtractor,
    DOCXExtractor,
    DOCExtractor,
    ExtractedChunk,
    normalize_text,
)
from .gdrive_service import GoogleDriveService

logger = logging.getLogger(__name__)


_db_migrated = False

def ensure_db_migrated():
    """Garante que as tabelas de banco de dados existam aplicando migrações automaticamente."""
    global _db_migrated
    if _db_migrated:
        return
    try:
        tables = connection.introspection.table_names()
        if "finder_files_documentchunk" not in tables:
            logger.info("[DB] Tabela finder_files_documentchunk não encontrada. Executando migrações automaticamente...")
            call_command("migrate", interactive=False)
        _db_migrated = True
    except Exception:
        _db_migrated = True


class IndexerService:
    def __init__(self):
        ensure_db_migrated()
        self.extractors = {
            '.pdf': PDFExtractor(),
            '.pptx': PPTXExtractor(),
            '.ppt': PPTExtractor(),
            '.docx': DOCXExtractor(),
            '.doc': DOCExtractor(),
        }

    def compute_file_hash(self, file_path: Path) -> str:
        """Calcula o MD5 do arquivo para detectar modificações de conteúdo."""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Erro ao calcular hash de {file_path}: {e}")
            return f"size_{file_path.stat().st_size}"

    def index_file(self, file_path: Path, source: str = IndexedFile.SOURCE_LOCAL, external_id: Optional[str] = None) -> Optional[IndexedFile]:
        ensure_db_migrated()
        file_path = Path(file_path).resolve()
        if not file_path.exists() or not file_path.is_file():
            logger.warning(f"Arquivo não encontrado para indexação: {file_path}")
            return None

        ext = file_path.suffix.lower()
        if ext not in self.extractors:
            logger.info(f"Formato não suportado ignorado: {file_path}")
            return None

        stat = file_path.stat()
        file_size = stat.st_size
        modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.get_current_timezone())
        file_hash = self.compute_file_hash(file_path)

        str_path = str(file_path)
        existing = IndexedFile.objects.filter(file_path=str_path).first()
        if existing and existing.status == IndexedFile.STATUS_INDEXED and existing.file_hash == file_hash and existing.chunks.count() > 0:
            if external_id and not existing.external_id:
                existing.external_id = external_id
                existing.save(update_fields=['external_id'])
            logger.info(f"Arquivo inalterado, pulando indexação: {file_path.name}")
            return existing

        folder_name = file_path.parent.name or str(file_path.parent)

        with transaction.atomic():
            indexed_file, created = IndexedFile.objects.get_or_create(
                file_path=str_path,
                defaults={
                    'file_name': file_path.name,
                    'extension': ext.lstrip('.'),
                    'folder_name': folder_name,
                    'source': source,
                    'external_id': external_id,
                    'file_hash': file_hash,
                    'file_size': file_size,
                    'modified_at': modified_at,
                    'status': IndexedFile.STATUS_PENDING,
                }
            )
            if not created:
                indexed_file.file_name = file_path.name
                indexed_file.extension = ext.lstrip('.')
                indexed_file.folder_name = folder_name
                indexed_file.source = source
                if external_id:
                    indexed_file.external_id = external_id
                indexed_file.file_hash = file_hash
                indexed_file.file_size = file_size
                indexed_file.modified_at = modified_at
                indexed_file.chunks.all().delete()

            extractor = self.extractors[ext]
            try:
                extracted_chunks = extractor.extract(file_path)
                chunk_objects = []
                for chunk in extracted_chunks:
                    norm = normalize_text(chunk.text)
                    if norm:
                        chunk_objects.append(
                            DocumentChunk(
                                indexed_file=indexed_file,
                                page_number=chunk.page_number,
                                slide_number=chunk.slide_number,
                                snippet_text=chunk.snippet,
                                normalized_text=norm,
                                chunk_index=chunk.chunk_index
                            )
                        )
                
                if chunk_objects:
                    DocumentChunk.objects.bulk_create(chunk_objects)
                    indexed_file.status = IndexedFile.STATUS_INDEXED
                    indexed_file.last_indexed_at = timezone.now()
                    indexed_file.error_message = None
                    indexed_file.save()
                    logger.info(f"Arquivo indexado com sucesso: {file_path.name} ({len(chunk_objects)} trechos)")
                else:
                    indexed_file.status = IndexedFile.STATUS_ERROR
                    indexed_file.error_message = "Nenhum texto pesquisável foi extraído do arquivo."
                    indexed_file.save()
                    logger.warning(f"Nenhum texto extraído do arquivo: {file_path.name}")
            except Exception as e:
                logger.error(f"Erro ao processar conteúdo de {file_path.name}: {e}")
                indexed_file.status = IndexedFile.STATUS_ERROR
                indexed_file.error_message = str(e)
                indexed_file.save()

        return indexed_file

    def index_directory(self, dir_path: Path, source: str = IndexedFile.SOURCE_LOCAL) -> List[IndexedFile]:
        ensure_db_migrated()
        dir_path = Path(dir_path)
        indexed_files = []
        if not dir_path.exists() or not dir_path.is_dir():
            return indexed_files

        ignored_dirs = {'.venv', 'venv', '.git', '__pycache__', 'build', 'dist', 'node_modules', '.cache', '$recycle.bin', 'system volume information'}
        supported_extensions = ('.ppt', '.pptx', '.doc', '.docx', '.pdf')
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d.lower() not in ignored_dirs and not d.startswith('.')]
            for file_name in files:
                p = Path(root) / file_name
                if p.suffix.lower() in supported_extensions:
                    res = self.index_file(p, source=source)
                    if res:
                        indexed_files.append(res)
        return indexed_files

    @sync_to_async
    def aindex_directory_and_drive(self, local_dir: Optional[str] = None, include_drive: bool = True, drive_url: Optional[str] = None) -> Dict[str, Any]:
        results = []
        if local_dir:
            p = Path(local_dir)
            if p.exists():
                results.extend(self.index_directory(p, source=IndexedFile.SOURCE_LOCAL))

        if include_drive:
            gdrive = GoogleDriveService()
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            drive_files = loop.run_until_complete(gdrive.list_and_sync_folder(folder_url_or_id=drive_url))
            for df in drive_files:
                meta = gdrive.file_metadata.get(str(df.resolve()), {})
                ext_id = meta.get("id")
                res = self.index_file(df, source=IndexedFile.SOURCE_GOOGLE_DRIVE, external_id=ext_id)
                if res:
                    results.append(res)

        return self.get_status()

    @sync_to_async
    def aget_status(self) -> Dict[str, int]:
        return self.get_status()

    def get_status(self) -> Dict[str, int]:
        ensure_db_migrated()
        total_files = IndexedFile.objects.count()
        indexed_files = IndexedFile.objects.filter(status=IndexedFile.STATUS_INDEXED).count()
        pending_files = IndexedFile.objects.filter(status=IndexedFile.STATUS_PENDING).count()
        error_files = IndexedFile.objects.filter(status=IndexedFile.STATUS_ERROR).count()
        total_chunks = DocumentChunk.objects.count()
        return {
            "total_files": total_files,
            "indexed_files": indexed_files,
            "pending_files": pending_files,
            "error_files": error_files,
            "total_chunks": total_chunks
        }


class IndexingProgressTracker:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.is_running = False
        self.status_message = "Pronto para indexar."
        self.progress_pct = 0
        self.files_processed = 0
        self.total_files = 0
        self.error = None
        self.completed = False
        self.new_files_indexed = 0

    def start(self, local_dir: Optional[str] = None, include_drive: bool = True, drive_url: Optional[str] = None) -> bool:
        if self.is_running:
            return False
        import threading
        self.is_running = True
        self.status_message = "Iniciando processo de indexação..."
        self.progress_pct = 5
        self.files_processed = 0
        self.total_files = 0
        self.error = None
        self.completed = False
        self.new_files_indexed = 0

        thread = threading.Thread(
            target=self._run,
            args=(local_dir, include_drive, drive_url),
            daemon=True
        )
        thread.start()
        return True

    def _run(self, local_dir: Optional[str], include_drive: bool, drive_url: Optional[str]):
        import asyncio
        indexer = IndexerService()
        try:
            # 1. Pastas locais se fornecidas
            if local_dir:
                p = Path(local_dir)
                if p.exists():
                    self.status_message = f"Varrendo pasta local: {p.name}..."
                    self.progress_pct = 10
                    local_files = [f for f in p.rglob("*.*") if f.suffix.lower() in ('.ppt', '.pptx', '.doc', '.docx', '.pdf')]
                    self.total_files += len(local_files)
                    for f in local_files:
                        res = indexer.index_file(f, source=IndexedFile.SOURCE_LOCAL)
                        if res and res.status == IndexedFile.STATUS_INDEXED:
                            self.new_files_indexed += 1
                        self.files_processed += 1
                        if self.total_files > 0:
                            self.progress_pct = min(90, int((self.files_processed / self.total_files) * 80) + 10)

            # 2. Google Drive se solicitado
            if include_drive:
                self.status_message = "Conectando ao Google Drive e listando arquivos..."
                self.progress_pct = 15
                gdrive = GoogleDriveService()

                def on_gdrive_sync_progress(msg: str, current: int, total: int):
                    self.status_message = msg
                    if total > 0:
                        pct = int((current / total) * 35) + 15
                        self.progress_pct = min(50, pct)

                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                drive_files = loop.run_until_complete(
                    gdrive.list_and_sync_folder(folder_url_or_id=drive_url, progress_callback=on_gdrive_sync_progress)
                )

                self.total_files += len(drive_files)
                for idx, df in enumerate(drive_files, start=1):
                    self.status_message = f"Indexando slides: {df.name[:40]} ({idx}/{len(drive_files)})..."
                    meta = gdrive.file_metadata.get(str(df.resolve()), {})
                    ext_id = meta.get("id")
                    res = indexer.index_file(df, source=IndexedFile.SOURCE_GOOGLE_DRIVE, external_id=ext_id)
                    if res and res.status == IndexedFile.STATUS_INDEXED:
                        self.new_files_indexed += 1
                    self.files_processed += 1
                    if self.total_files > 0:
                        self.progress_pct = min(98, int((self.files_processed / self.total_files) * 48) + 50)

            self.status_message = f"Concluído com sucesso! {self.new_files_indexed} arquivos indexados."
            self.progress_pct = 100
            self.completed = True
        except Exception as e:
            logger.error(f"[IndexingManager] Erro durante indexação: {e}", exc_info=True)
            self.error = str(e)
            self.status_message = f"Erro durante a indexação: {e}"
        finally:
            self.is_running = False

    def get_progress(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "status_message": self.status_message,
            "progress_pct": self.progress_pct,
            "files_processed": self.files_processed,
            "total_files": self.total_files,
            "new_files_indexed": self.new_files_indexed,
            "completed": self.completed,
            "error": self.error
        }


class FileSearchService:
    def __init__(self):
        ensure_db_migrated()

    @sync_to_async
    def asearch(self, query: str) -> List[Dict[str, Any]]:
        return self.search(query)

    def search(self, query: str) -> List[Dict[str, Any]]:
        ensure_db_migrated()
        query = query.strip()
        words = [w for w in query.split() if w]
        min_words = getattr(settings, "MIN_SEARCH_WORDS", 2)
        if len(words) < min_words:
            return []

        stopwords = {
            'a', 'o', 'as', 'os', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'nos', 'nas',
            'por', 'pelo', 'pela', 'pelos', 'pelas', 'para', 'pra', 'pro', 'pras', 'pros',
            'com', 'e', 'ou', 'se', 'um', 'uma', 'uns', 'umas', 'que', 'ao', 'aos',
            'me', 'te', 'lhe', 'dele', 'dela', 'deles', 'delas', 'este', 'esta', 'isto'
        }

        norm_query = normalize_text(query)
        norm_words = [normalize_text(w) for w in words if normalize_text(w)]

        # Filtra stopwords triviais para identificar palavras-chave de conteúdo
        content_words = [w for w in norm_words if w not in stopwords and len(w) > 1]
        if not content_words:
            content_words = [w for w in norm_words if len(w) > 1] or norm_words

        unique_content = list(dict.fromkeys(content_words))
        total_content = len(unique_content)

        # Filtro em nível de banco de dados para acelerar buscas (evita varrer 100k linhas em memória)
        distinctive_terms = [w for w in unique_content if len(w) >= 4] or unique_content
        db_filter = Q()
        if len(norm_query) >= 3:
            db_filter |= Q(normalized_text__icontains=norm_query)
        for term in distinctive_terms:
            db_filter |= Q(normalized_text__icontains=term)

        chunks_qs = DocumentChunk.objects.filter(
            indexed_file__status=IndexedFile.STATUS_INDEXED
        ).filter(db_filter).select_related('indexed_file').order_by('indexed_file_id', 'slide_number', 'page_number')

        results = []
        seen_keys = set()

        for chunk in chunks_qs:
            text = chunk.normalized_text
            if not text:
                continue

            exact_phrase = norm_query in text

            # Conjunto de palavras completas do texto do slide (evita falsos positivos por substring)
            text_tokens = set(re.findall(r'\b\w+\b', text))
            matched_words = [w for w in unique_content if w in text_tokens]
            matched_count = len(matched_words)

            is_accepted = False
            if exact_phrase:
                is_accepted = True
            elif total_content <= 3:
                # Consultas de até 3 termos (ex: "tende piedade", "damos graças"): exige todos os termos
                is_accepted = (matched_count == total_content)
            elif total_content == 4:
                # 4 termos (ex: "Maria, és a escolhida de Deus"):
                # Exige pelo menos 3 termos E pelo menos um termo distintivo (>= 5 letras)
                has_distinctive = any(len(w) >= 5 and w in matched_words for w in unique_content)
                is_accepted = (matched_count >= 3) and has_distinctive
            else:
                # 5+ termos: exige >= 75% dos termos e pelo menos um termo distintivo
                has_distinctive = any(len(w) >= 5 and w in matched_words for w in unique_content)
                required = max(3, int(total_content * 0.75))
                is_accepted = (matched_count >= required) and has_distinctive

            if not is_accepted:
                continue

            score = (matched_count / total_content) * 60.0
            if exact_phrase:
                score += 100.0

            file_norm = normalize_text(chunk.indexed_file.file_name)
            if any(w in file_norm for w in unique_content if len(w) >= 4):
                score += 25.0

            loc_num = chunk.slide_number if chunk.slide_number is not None else chunk.page_number
            if chunk.slide_number is not None:
                location_str = f"Slide {chunk.slide_number}"
            elif chunk.page_number is not None:
                location_str = f"Página {chunk.page_number}"
            else:
                location_str = "Documento"

            # Determina URL de abertura
            open_url = ""
            if chunk.indexed_file.source == IndexedFile.SOURCE_GOOGLE_DRIVE:
                if chunk.indexed_file.external_id:
                    open_url = f"https://drive.google.com/file/d/{chunk.indexed_file.external_id}/view"
                else:
                    open_url = getattr(settings, "PASTA_DRIVE", "")
            if not open_url:
                open_url = Path(chunk.indexed_file.file_path).as_uri() if Path(chunk.indexed_file.file_path).exists() else ""

            # Deduplicação de refrão/música repetida no mesmo arquivo (ex: slide 2, 4, 6):
            # Mostra apenas o primeiro slide onde o refrão/música aparece no arquivo
            lines = [normalize_text(l) for l in chunk.snippet_text.splitlines() if len(normalize_text(l)) > 4]
            matching_lines = [l for l in lines if any(w in l for w in unique_content)]
            song_signature = matching_lines[0][:50] if matching_lines else "".join(text.split())[:50]
            repeat_key = (chunk.indexed_file.id, song_signature)

            if repeat_key not in seen_keys:
                seen_keys.add(repeat_key)
                results.append({
                    "file_name": chunk.indexed_file.file_name,
                    "folder_name": chunk.indexed_file.folder_name,
                    "source": chunk.indexed_file.source,
                    "location": location_str,
                    "page": loc_num,
                    "slide": loc_num,
                    "snippet": chunk.snippet_text,
                    "score": round(score, 2),
                    "file_path": chunk.indexed_file.file_path,
                    "open_url": open_url,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        max_results = getattr(settings, "MAX_SEARCH_RESULTS", 50)
        return results[:max_results]

    @sync_to_async
    def aget_suggestions(self, prefix: str, limit: int = 15) -> List[str]:
        return self.get_suggestions(prefix, limit)

    def get_suggestions(self, prefix: str, limit: int = 15) -> List[str]:
        ensure_db_migrated()
        prefix = prefix.strip()
        if len(prefix) < 2:
            return []

        norm_prefix = normalize_text(prefix)
        suggestions = []
        seen = set()

        # 1. Sugestões por nome de arquivo / apresentação
        files = IndexedFile.objects.filter(
            status=IndexedFile.STATUS_INDEXED,
            file_name__icontains=prefix
        ).values_list('file_name', flat=True)[:limit]

        for fname in files:
            clean_title = Path(fname).stem
            if clean_title.lower() not in seen and not clean_title.startswith("default"):
                seen.add(clean_title.lower())
                suggestions.append(clean_title)
                if len(suggestions) >= limit:
                    return suggestions

        # 2. Sugestões por trecho de documento / canto
        chunks = DocumentChunk.objects.filter(
            normalized_text__icontains=norm_prefix
        ).values_list('snippet_text', flat=True)[:limit * 6]

        for snippet in chunks:
            lines = [l.strip() for l in snippet.split('\n') if l.strip()]
            for line in lines:
                norm_line = normalize_text(line)
                if norm_prefix in norm_line:
                    clean_sug = line[:60].strip(" -–.,;:\"'0123456789")
                    if (
                        len(clean_sug) >= 4
                        and any(c.isalpha() for c in clean_sug)
                        and " " in clean_sug
                        and not any(c in clean_sug for c in ['<', '>', '{', '}', '\\', '/', '='])
                        and clean_sug.lower() not in seen
                    ):
                        seen.add(clean_sug.lower())
                        suggestions.append(clean_sug)
                        if len(suggestions) >= limit:
                            return suggestions

        return suggestions[:limit]

