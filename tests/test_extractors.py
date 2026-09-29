import pytest
from pathlib import Path
from finder_files.extractors import PDFExtractor, PPTXExtractor, DOCXExtractor

def test_pdf_extractor_non_existent_file(tmp_path):
    extractor = PDFExtractor()
    chunks = extractor.extract(tmp_path / "non_existent.pdf")
    assert chunks == []


def test_pptx_extractor_non_existent_file(tmp_path):
    extractor = PPTXExtractor()
    chunks = extractor.extract(tmp_path / "non_existent.pptx")
    assert chunks == []


def test_docx_extractor_non_existent_file(tmp_path):
    extractor = DOCXExtractor()
    chunks = extractor.extract(tmp_path / "non_existent.docx")
    assert chunks == []
