import time
from typing import List, Optional
from ninja import NinjaAPI, Schema
from pydantic import Field
from django.conf import settings
from .services import FileSearchService, IndexerService, IndexingProgressTracker

api = NinjaAPI(
    title="API Buscador de Músicas",
    version="1.0.0",
    description="API assíncrona para busca determinística e semântica de músicas em apresentações e documentos."
)


class SearchRequest(Schema):
    query: str = Field(..., min_length=1, description="Termo de busca com no mínimo 2 palavras")


class SearchResultItem(Schema):
    file_name: str
    folder_name: str
    source: str
    location: str
    page: Optional[int] = None
    slide: Optional[int] = None
    snippet: str
    score: float = 0.0
    file_path: str
    open_url: Optional[str] = None


class SearchResponse(Schema):
    results: List[SearchResultItem]
    total: int
    query: str
    duration_ms: float
    error: Optional[str] = None


class IndexScanRequest(Schema):
    folder_path: Optional[str] = None
    include_drive: bool = True
    drive_url: Optional[str] = None


class IndexStatusResponse(Schema):
    total_files: int
    indexed_files: int
    pending_files: int
    error_files: int
    total_chunks: int


class IndexScanResponse(Schema):
    status: str
    message: str


class IndexingProgressResponse(Schema):
    is_running: bool
    status_message: str
    progress_pct: int
    files_processed: int
    total_files: int
    new_files_indexed: int
    completed: bool
    error: Optional[str] = None


@api.get("/health", tags=["Health"])
async def health_check(request):
    return {"status": "ok", "service": "Buscador de Músicas"}


@api.get("/search/suggestions", response=List[str], tags=["Search"])
async def get_search_suggestions(request, q: str = ""):
    if not q or len(q.strip()) < 2:
        return []
    search_service = FileSearchService()
    return await search_service.aget_suggestions(q.strip(), limit=15)


@api.post("/search", response=SearchResponse, tags=["Search"])
async def search_documents(request, payload: SearchRequest):
    start_time = time.time()
    query = payload.query.strip()
    words = [w for w in query.split() if w]

    min_words = getattr(settings, "MIN_SEARCH_WORDS", 2)
    if len(words) < min_words:
        return SearchResponse(
            results=[],
            total=0,
            query=query,
            duration_ms=(time.time() - start_time) * 1000,
            error=f"A busca deve conter no mínimo {min_words} palavras."
        )

    search_service = FileSearchService()
    results = await search_service.asearch(query)
    duration = (time.time() - start_time) * 1000

    return SearchResponse(
        results=results,
        total=len(results),
        query=query,
        duration_ms=duration
    )


@api.post("/index/scan", response=IndexScanResponse, tags=["Indexing"])
async def trigger_indexing(request, payload: IndexScanRequest):
    tracker = IndexingProgressTracker.get_instance()
    started = tracker.start(
        local_dir=payload.folder_path,
        include_drive=payload.include_drive,
        drive_url=payload.drive_url
    )
    return IndexScanResponse(
        status="started" if started else "already_running",
        message="Indexação iniciada com sucesso em segundo plano!" if started else "Uma indexação já está em andamento."
    )


@api.get("/index/progress", response=IndexingProgressResponse, tags=["Indexing"])
async def get_indexing_progress(request):
    tracker = IndexingProgressTracker.get_instance()
    return tracker.get_progress()


@api.get("/index/status", response=IndexStatusResponse, tags=["Indexing"])
async def get_index_status(request):
    indexer = IndexerService()
    return await indexer.aget_status()


class OpenLocalFileRequest(Schema):
    file_path: str


@api.post("/files/open-local", tags=["Files"])
def open_local_file(request, payload: OpenLocalFileRequest):
    import subprocess
    import os
    from pathlib import Path
    p = Path(payload.file_path)
    if not p.exists():
        return {"status": "error", "message": "Arquivo não encontrado no disco local."}
    
    if os.name == 'nt':
        subprocess.Popen(f'explorer /select,"{p.resolve()}"')
        return {"status": "ok", "message": "Pasta aberta no Explorer com o arquivo selecionado."}
    return {"status": "ok", "message": "Sucesso."}

