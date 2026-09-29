import os
import re
import logging
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

def is_valid_file_content(content: bytes, ext: str) -> bool:
    """Verifica se o conteúdo baixado é um arquivo binário válido e não uma página HTML de erro/login."""
    if not content or len(content) < 100:
        return False
    head_start = content[:300].lower()
    if b"<!doctype html" in head_start or b"<html" in head_start or b"servicelogin" in head_start:
        return False
    
    ext = ext.lower()
    if ext in ('.pptx', '.docx'):
        return content.startswith(b"PK\x03\x04") or b"[Content_Types].xml" in content[:2000]
    elif ext == '.pdf':
        return content.startswith(b"%PDF")
    elif ext in ('.ppt', '.doc'):
        return content.startswith(b"\xd0\xcf\x11\xe0") or len(content) > 500
    return True


class GoogleDriveService:
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (settings.BASE_DIR / ".cache" / "gdrive")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.file_metadata: Dict[str, Dict[str, Any]] = {}
        self._composio_client = None
        self.composio_account_id = None
        self.composio_user_id = None
        self._init_composio()

    def _init_composio(self):
        composio_api_key = getattr(settings, "API_KEY_COMPOSIO", "") or os.getenv("API_KEY_COMPOSIO", "") or os.getenv("COMPOSIO_API_KEY", "")
        if not composio_api_key:
            return
        os.environ["COMPOSIO_API_KEY"] = composio_api_key
        try:
            from composio import Composio
            self._composio_client = Composio(api_key=composio_api_key)
            self.composio_account_id = getattr(settings, "ACCOUNT_ID_COMPOSIO", "") or os.getenv("ACCOUNT_ID_COMPOSIO", "")
            self.composio_user_id = getattr(settings, "COMPOSIO_USER", "") or os.getenv("COMPOSIO_USER", "")
            logger.info("[GoogleDriveService] Composio client inicializado com sucesso.")
        except Exception as e:
            logger.warning(f"[GoogleDriveService] Falha ao inicializar SDK Composio: {e}")
            self._composio_client = None

    def _list_files_via_composio(self, root_folder_id: str) -> List[Tuple[str, str, Path, Optional[str]]]:
        """
        Usa o Composio para listar recursivamente todos os arquivos suportados nas pastas do Google Drive.
        Retorna lista de (file_id, file_name, rel_dir, web_view_link).
        """
        if not self._composio_client:
            return []

        supported_extensions = ('.ppt', '.pptx', '.doc', '.docx', '.pdf')
        all_found: List[Tuple[str, str, Path, Optional[str]]] = []
        folder_queue: List[Tuple[str, Path]] = [(root_folder_id, Path(""))]
        visited_folders: Set[str] = set()

        while folder_queue and len(visited_folders) < 100:
            current_folder_id, rel_dir = folder_queue.pop(0)
            if current_folder_id in visited_folders:
                continue
            visited_folders.add(current_folder_id)

            page_token = None
            while True:
                args: Dict[str, Any] = {
                    "q": f"'{current_folder_id}' in parents and trashed = false",
                    "pageSize": 100,
                    "fields": "nextPageToken, files(id, name, mimeType, webViewLink)"
                }
                if page_token:
                    args["pageToken"] = page_token

                call_kwargs: Dict[str, Any] = {
                    "slug": "GOOGLEDRIVE_LIST_FILES",
                    "arguments": args,
                    "dangerously_skip_version_check": True
                }
                if self.composio_account_id:
                    call_kwargs["connected_account_id"] = self.composio_account_id
                if self.composio_user_id:
                    call_kwargs["user_id"] = self.composio_user_id

                try:
                    resp = self._composio_client.tools.execute(**call_kwargs)
                except Exception as comp_err:
                    logger.error(f"[GoogleDriveService - Composio] Exceção ao listar pasta {current_folder_id}: {comp_err}")
                    break

                if not resp or not resp.get("successful", False):
                    logger.warning(f"[GoogleDriveService - Composio] Falha ao listar pasta {current_folder_id}: {resp.get('error') if resp else 'No response'}")
                    break

                data = resp.get("data", {})
                files = data.get("files", [])
                for item in files:
                    name = item.get("name", "")
                    mime = item.get("mimeType", "")
                    fid = item.get("id")
                    if not fid or not name:
                        continue

                    if mime == "application/vnd.google-apps.folder":
                        safe_sub = re.sub(r'[\\/*?:"<>|]', "_", name)
                        folder_queue.append((fid, rel_dir / safe_sub))
                    else:
                        ext = Path(name).suffix.lower()
                        if not ext:
                            if "presentation" in mime or "powerpoint" in mime:
                                ext = ".pptx"
                            elif "document" in mime or "word" in mime:
                                ext = ".docx"
                            elif "pdf" in mime:
                                ext = ".pdf"
                        if ext in supported_extensions:
                            all_found.append((fid, name, rel_dir, item.get("webViewLink")))

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        return all_found

    @staticmethod
    def extract_folder_id(url_or_id: str) -> Optional[str]:
        if not url_or_id:
            return None
        url_or_id = url_or_id.strip()
        if re.match(r'^[a-zA-Z0-9_-]{25,}$', url_or_id):
            return url_or_id
        match = re.search(r'folders/([a-zA-Z0-9_-]+)', url_or_id)
        if match:
            return match.group(1)
        match_id = re.search(r'id=([a-zA-Z0-9_-]+)', url_or_id)
        if match_id:
            return match_id.group(1)
        return None

    def _extract_items_from_html(self, text: str) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str, str]]]:
        """
        Extrai subpastas e arquivos do HTML retornado pelo Google Drive.
        Retorna (subpastas, arquivos), onde:
        subpastas = [(id, nome)]
        arquivos = [(id, nome, mime_type_ou_ext)]
        """
        unescaped = text.replace(r'\x22', '"').replace(r'\x5b', '[').replace(r'\x5d', ']').replace(r'\/', '/')
        
        folders: List[Tuple[str, str]] = []
        files: List[Tuple[str, str, str]] = []
        seen_ids: Set[str] = set()

        # Padrão 1: ["ID", ["PARENT_ID"], "NAME", "MIME_TYPE", ...]
        matches1 = re.findall(r'\["([a-zA-Z0-9_-]{25,50})",\["[a-zA-Z0-9_-]{25,50}"\],"([^"]+)","([^"]+)"', unescaped)
        for fid, raw_name, mime in matches1:
            if fid in seen_ids:
                continue
            seen_ids.add(fid)
            name = urllib.parse.unquote(raw_name)
            if "folder" in mime or mime == "application/vnd.google-apps.folder":
                folders.append((fid, name))
            else:
                files.append((fid, name, mime))

        # Padrão 2: ["ID", "NAME", "MIME_TYPE", ...]
        matches2 = re.findall(r'\["([a-zA-Z0-9_-]{25,50})","([^"]+)","([^"]+)"', unescaped)
        for fid, raw_name, mime in matches2:
            if fid in seen_ids:
                continue
            name = urllib.parse.unquote(raw_name)
            if len(name) < 2 or name.startswith("http"):
                continue
            seen_ids.add(fid)
            if "folder" in mime or mime == "application/vnd.google-apps.folder":
                folders.append((fid, name))
            else:
                files.append((fid, name, mime))

        # Padrão 3: fallback para arquivos com extensão explícita
        matches_ext = re.findall(r'\["([a-zA-Z0-9_-]{25,50})",\["([^"]+\.(?:ppt|pptx|doc|docx|pdf))"', unescaped, re.IGNORECASE)
        for fid, fname in matches_ext:
            if fid not in seen_ids:
                seen_ids.add(fid)
                files.append((fid, fname, Path(fname).suffix.lower()))

        return folders, files

    async def list_and_sync_folder(
        self,
        folder_url_or_id: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> List[Path]:
        """
        Sincroniza recursivamente arquivos da pasta do Google Drive e suas subpastas.
        Retorna lista de caminhos locais dos arquivos sincronizados no cache.
        """
        folder_input = folder_url_or_id or getattr(settings, "PASTA_DRIVE", "")
        root_folder_id = self.extract_folder_id(folder_input)
        synced_files: List[Path] = []

        if not root_folder_id:
            logger.warning("[GoogleDriveService] Nenhuma URL ou ID de pasta do Google Drive configurado.")
            return [p for p in self.cache_dir.rglob("*.*") if p.is_file() and p.suffix.lower() in ('.ppt', '.pptx', '.doc', '.docx', '.pdf')]

        all_found_files: List[Any] = []

        if progress_callback:
            progress_callback("Conectando ao Google Drive...", 0, 0)

        # 1. Tenta varredura autenticada via Composio se configurado
        if self._composio_client:
            try:
                logger.info(f"[GoogleDriveService] Iniciando sincronização via Composio para pasta ID {root_folder_id}...")
                if progress_callback:
                    progress_callback("Varrendo pastas via Google Drive API...", 0, 0)
                all_found_files = self._list_files_via_composio(root_folder_id)
                logger.info(f"[GoogleDriveService] Composio encontrou {len(all_found_files)} arquivos válidos.")
            except Exception as e:
                logger.error(f"[GoogleDriveService] Erro durante busca via Composio: {e}. Usando crawler público como fallback.")
                all_found_files = []

        try:
            async with httpx.AsyncClient(timeout=40.0, follow_redirects=True, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }) as client:
                # 2. Se Composio não encontrou arquivos ou não configurado, faz crawling público
                if not all_found_files:
                    if progress_callback:
                        progress_callback("Varrendo arquivos do Google Drive...", 0, 0)
                    folder_queue: List[Tuple[str, Path]] = [(root_folder_id, Path(""))]
                    visited_folders: Set[str] = set()

                    while folder_queue and len(visited_folders) < 50:
                        current_folder_id, rel_dir = folder_queue.pop(0)
                        if current_folder_id in visited_folders:
                            continue
                        visited_folders.add(current_folder_id)

                        page_url = f"https://drive.google.com/drive/folders/{current_folder_id}"
                        try:
                            resp = await client.get(page_url)
                            if resp.status_code != 200:
                                logger.warning(f"[GoogleDriveService] Falha HTTP {resp.status_code} para pasta ID: {current_folder_id}")
                                continue
                            
                            subfolders, files = self._extract_items_from_html(resp.text)
                            logger.info(f"[GoogleDriveService] Pasta '{rel_dir}' (ID: {current_folder_id}): {len(subfolders)} subpastas, {len(files)} arquivos")

                            for sub_id, sub_name in subfolders:
                                if sub_id not in visited_folders:
                                    safe_sub_name = re.sub(r'[\\/*?:"<>|]', "_", sub_name)
                                    folder_queue.append((sub_id, rel_dir / safe_sub_name))

                            for fid, fname, mime in files:
                                ext = Path(fname).suffix.lower()
                                if not ext:
                                    if "presentation" in mime or "powerpoint" in mime:
                                        ext = ".pptx"
                                    elif "document" in mime or "word" in mime:
                                        ext = ".docx"
                                    elif "pdf" in mime:
                                        ext = ".pdf"
                                    else:
                                        ext = ".pptx"
                                
                                if ext in ('.ppt', '.pptx', '.doc', '.docx', '.pdf'):
                                    all_found_files.append((fid, fname, rel_dir, None))

                        except Exception as f_err:
                            logger.error(f"[GoogleDriveService] Erro ao listar pasta ID {current_folder_id}: {f_err}")

                # 3. Baixa os arquivos encontrados concorrentemente (até 5 simultâneos)
                total_dl = len(all_found_files)
                logger.info(f"[GoogleDriveService] Total de arquivos para sincronizar: {total_dl}")
                if progress_callback:
                    progress_callback(f"Verificando {total_dl} arquivos do Drive...", 0, total_dl)

                import asyncio
                semaphore = asyncio.Semaphore(5)
                dl_counter = 0

                async def download_single_file(item):
                    nonlocal dl_counter
                    if len(item) == 4:
                        file_id, file_name, rel_dir, web_view_link = item
                    else:
                        file_id, file_name, rel_dir = item[:3]
                        web_view_link = None

                    safe_name = re.sub(r'[\\/*?:"<>|]', "_", file_name)
                    ext = Path(safe_name).suffix.lower() or ".pptx"
                    if not safe_name.endswith(ext):
                        safe_name += ext

                    dest_dir = self.cache_dir / rel_dir
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    dest_path = dest_dir / safe_name

                    self.file_metadata[str(dest_path.resolve())] = {
                        "id": file_id,
                        "name": file_name,
                        "web_view_link": web_view_link or f"https://drive.google.com/file/d/{file_id}/view"
                    }

                    if not dest_path.exists() or dest_path.stat().st_size == 0 or not is_valid_file_content(dest_path.read_bytes(), ext):
                        async with semaphore:
                            if ext == '.ppt':
                                download_urls = [
                                    f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t",
                                    f"https://drive.google.com/uc?export=download&id={file_id}",
                                    f"https://docs.google.com/presentation/d/{file_id}/export/pptx",
                                ]
                            elif ext in ('.doc', '.docx'):
                                download_urls = [
                                    f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t",
                                    f"https://docs.google.com/document/d/{file_id}/export?format=docx",
                                    f"https://drive.google.com/uc?export=download&id={file_id}",
                                ]
                            elif ext == '.pdf':
                                download_urls = [
                                    f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t",
                                    f"https://drive.google.com/uc?export=download&id={file_id}",
                                ]
                            else:  # .pptx
                                download_urls = [
                                    f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t",
                                    f"https://docs.google.com/presentation/d/{file_id}/export/pptx",
                                    f"https://drive.google.com/uc?export=download&id={file_id}",
                                ]
                            
                            downloaded_ok = False
                            for dl_url in download_urls:
                                try:
                                    f_resp = await client.get(dl_url)
                                    if f_resp.status_code == 200 and is_valid_file_content(f_resp.content, ext):
                                        dest_path.write_bytes(f_resp.content)
                                        downloaded_ok = True
                                        logger.info(f"[GoogleDriveService] Download concluído: {dest_path}")
                                        break
                                except Exception as dl_err:
                                    logger.debug(f"[GoogleDriveService] Tentativa {dl_url} falhou: {dl_err}")

                            if not downloaded_ok:
                                logger.warning(f"[GoogleDriveService] Falha no download do arquivo {file_name} (ID: {file_id})")

                    dl_counter += 1
                    if progress_callback:
                        progress_callback(f"Sincronizando arquivo {dl_counter}/{total_dl}: {file_name[:35]}", dl_counter, total_dl)

                    if dest_path.exists() and dest_path.stat().st_size > 0 and is_valid_file_content(dest_path.read_bytes(), ext):
                        return dest_path
                    return None

                download_tasks = [download_single_file(item) for item in all_found_files]
                results = await asyncio.gather(*download_tasks, return_exceptions=True)
                for r in results:
                    if isinstance(r, Path) and r not in synced_files:
                        synced_files.append(r)

        except Exception as e:
            logger.error(f"[GoogleDriveService] Erro durante sincronização do Google Drive: {e}")

        # Inclui todos os arquivos válidos presentes no cache local
        existing_cached = [p for p in self.cache_dir.rglob("*.*") if p.is_file() and p.suffix.lower() in ('.ppt', '.pptx', '.doc', '.docx', '.pdf')]
        for p in existing_cached:
            if p not in synced_files and is_valid_file_content(p.read_bytes(), p.suffix):
                synced_files.append(p)

        return synced_files
