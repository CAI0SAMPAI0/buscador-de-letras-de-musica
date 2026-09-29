import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from finder_files.gdrive_service import GoogleDriveService
from finder_files.services import FileSearchService
from finder_files.models import IndexedFile, DocumentChunk

@pytest.mark.django_db
def test_gdrive_service_composio_init(settings):
    settings.API_KEY_COMPOSIO = "mock_api_key"
    settings.ACCOUNT_ID_COMPOSIO = "acc_123"
    settings.COMPOSIO_USER = "usr_456"

    with patch("composio.Composio") as mock_composio_cls:
        service = GoogleDriveService(cache_dir=Path("./test_cache"))
        assert service._composio_client is not None
        assert service.composio_account_id == "acc_123"
        assert service.composio_user_id == "usr_456"


@pytest.mark.django_db
def test_composio_file_listing_and_metadata():
    service = GoogleDriveService(cache_dir=Path("./test_cache"))
    mock_client = MagicMock()
    service._composio_client = mock_client
    service.composio_account_id = "acc_test"
    service.composio_user_id = "user_test"

    # Simula resposta do Composio com 1 subpasta e 1 arquivo
    mock_client.tools.execute.side_effect = [
        {
            "successful": True,
            "data": {
                "files": [
                    {
                        "id": "subfolder_id_123",
                        "name": "2026",
                        "mimeType": "application/vnd.google-apps.folder"
                    },
                    {
                        "id": "file_id_root",
                        "name": "Canto Inicial.pptx",
                        "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        "webViewLink": "https://drive.google.com/file/d/file_id_root/view"
                    }
                ],
                "nextPageToken": None
            }
        },
        {
            "successful": True,
            "data": {
                "files": [
                    {
                        "id": "file_id_sub",
                        "name": "Gloria a Deus.pptx",
                        "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        "webViewLink": "https://drive.google.com/file/d/file_id_sub/view"
                    }
                ],
                "nextPageToken": None
            }
        }
    ]

    files = service._list_files_via_composio("root_folder_id")
    assert len(files) == 2
    fids = [f[0] for f in files]
    assert "file_id_root" in fids
    assert "file_id_sub" in fids


@pytest.mark.django_db
def test_external_id_in_search_open_url(tmp_path):
    test_file = tmp_path / "Missa_Teste.pptx"
    test_file.write_text("dummy")

    indexed = IndexedFile.objects.create(
        file_path=str(test_file),
        file_name="Missa_Teste.pptx",
        folder_name="2026",
        source=IndexedFile.SOURCE_GOOGLE_DRIVE,
        external_id="google_drive_file_id_999",
        status=IndexedFile.STATUS_INDEXED
    )
    assert indexed.external_id == "google_drive_file_id_999"

    # Cria DocumentChunk com texto para busca
    DocumentChunk.objects.create(
        indexed_file=indexed,
        page_number=1,
        slide_number=2,
        snippet_text="Senhor, tende piedade de nós e perdoai nossos pecados",
        normalized_text="senhor tende piedade de nos e perdoai nossos pecados",
        chunk_index=0
    )

    searcher = FileSearchService()
    results = searcher.search("tende piedade")
    assert len(results) >= 1
    match = results[0]
    assert match["file_name"] == "Missa_Teste.pptx"
    assert match["open_url"] == "https://drive.google.com/file/d/google_drive_file_id_999/view"
