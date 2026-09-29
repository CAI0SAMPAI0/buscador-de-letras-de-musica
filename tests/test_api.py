import pytest
from ninja.testing import TestAsyncClient
from finder_files.api import api
from finder_files.models import IndexedFile, DocumentChunk
from finder_files.extractors.base import normalize_text

client = TestAsyncClient(api)

@pytest.mark.asyncio
async def test_api_health():
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Buscador de Músicas"}


@pytest.mark.asyncio
async def test_api_search_validation_short_query():
    response = await client.post("/search", json={"query": "Santo"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert "no mínimo 2 palavras" in data["error"]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_api_search_valid_query(db):
    idx_file = await IndexedFile.objects.acreate(
        file_name="Canto_Entrada.pdf",
        extension="pdf",
        file_path="C:/Musicas/Canto_Entrada.pdf",
        folder_name="Musicas",
        source="local",
        status=IndexedFile.STATUS_INDEXED
    )
    await DocumentChunk.objects.acreate(
        indexed_file=idx_file,
        page_number=5,
        snippet_text="Vem a mim, Senhor, com tua graça infinita",
        normalized_text=normalize_text("Vem a mim, Senhor, com tua graça infinita"),
        chunk_index=0
    )

    response = await client.post("/search", json={"query": "Vem Senhor"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["file_name"] == "Canto_Entrada.pdf"
    assert data["results"][0]["page"] == 5
    assert data["results"][0]["location"] == "Página 5"
    assert "open_url" in data["results"][0]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_api_search_suggestions(db):
    idx_file = await IndexedFile.objects.acreate(
        file_name="Gloria_Liturgico.pptx",
        extension="pptx",
        file_path="C:/Musicas/Gloria_Liturgico.pptx",
        folder_name="2026",
        source="local",
        status=IndexedFile.STATUS_INDEXED
    )
    await DocumentChunk.objects.acreate(
        indexed_file=idx_file,
        slide_number=1,
        snippet_text="Glória a Deus nas alturas e paz na terra",
        normalized_text=normalize_text("Glória a Deus nas alturas e paz na terra"),
        chunk_index=0
    )

    response = await client.get("/search/suggestions?q=Glo")
    assert response.status_code == 200
    suggestions = response.json()
    assert isinstance(suggestions, list)
    assert len(suggestions) <= 4
    assert any("Gloria" in s or "Glória" in s for s in suggestions)

