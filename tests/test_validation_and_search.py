import pytest
from finder_files.extractors.base import normalize_text
from finder_files.services import FileSearchService
from finder_files.models import IndexedFile, DocumentChunk

@pytest.mark.django_db
def test_search_query_minimum_words_validation(db):
    service = FileSearchService()

    # Consulta com menos de 2 palavras (1 palavra) deve retornar lista vazia
    results_one = service.search("Santo")
    assert len(results_one) == 0

    # Consulta com 2 ou mais palavras deve ser aceita
    results_two = service.search("Santo Santo")
    assert isinstance(results_two, list)


def test_text_normalization():
    assert normalize_text("Glória a Deus nas Alturas!") == "gloria a deus nas alturas!"
    assert normalize_text("CORAÇÃO DE JESUS") == "coracao de jesus"
    assert normalize_text("    pão da vida   ") == "pao da vida"


@pytest.mark.django_db
def test_search_returns_ranked_results(db):
    idx_file = IndexedFile.objects.create(
        file_name="Missa_Domingo_Exclusivo.pptx",
        extension="pptx",
        file_path="C:/Misas/Missa_Domingo_Exclusivo.pptx",
        folder_name="Misas",
        source="local",
        status=IndexedFile.STATUS_INDEXED
    )

    DocumentChunk.objects.create(
        indexed_file=idx_file,
        slide_number=3,
        snippet_text="Santo, Santo, Santo, Senhor Deus do Universo Exclusivo",
        normalized_text=normalize_text("Santo, Santo, Santo, Senhor Deus do Universo Exclusivo"),
        chunk_index=0
    )

    service = FileSearchService()
    results = service.search("Santo Exclusivo")

    assert len(results) >= 1
    top_result = results[0]
    assert top_result["file_name"] == "Missa_Domingo_Exclusivo.pptx"
    assert top_result["slide"] == 3
    assert top_result["location"] == "Slide 3"
    assert top_result["score"] > 0


@pytest.mark.django_db
def test_phrase_search_precision_and_no_false_positives(db):
    idx_file = IndexedFile.objects.create(
        file_name="Gloria_Missa_2017.pptx",
        extension="pptx",
        file_path="C:/Misas/Gloria_Missa_2017.pptx",
        folder_name="2017",
        source="google_drive",
        status=IndexedFile.STATUS_INDEXED
    )

    # Chunk A: Contém 'nós', 'vos', 'damos', mas NÃO contém 'graças'
    chunk_a = DocumentChunk.objects.create(
        indexed_file=idx_file,
        slide_number=2,
        snippet_text="2. Deus e Pai, nós vos louvamos, adoramos, bendizemos; damos glória ao vosso nome.",
        normalized_text=normalize_text("2. Deus e Pai, nós vos louvamos, adoramos, bendizemos; damos glória ao vosso nome."),
        chunk_index=0
    )

    # Chunk B: Contém a frase completa com 'graças'
    chunk_b = DocumentChunk.objects.create(
        indexed_file=idx_file,
        slide_number=5,
        snippet_text="Senhor Deus, nós vos damos graças, por vossa imensa glória.",
        normalized_text=normalize_text("Senhor Deus, nós vos damos graças, por vossa imensa glória."),
        chunk_index=1
    )

    service = FileSearchService()
    results = service.search("nós vos damos graças")

    # Deve conter Chunk B e NÃO deve conter Chunk A como falso positivo
    slides_found = [r["slide"] for r in results]
    assert 5 in slides_found
    assert 2 not in slides_found
