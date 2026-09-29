import asyncio
from django.core.management.base import BaseCommand
from finder_files.services import IndexerService

class Command(BaseCommand):
    help = "Indexa arquivos de pastas locais e/ou do Google Drive na base de dados SQLite."

    def add_arguments(self, parser):
        parser.add_argument("--local-dir", type=str, help="Caminho de uma pasta local para indexar")
        parser.add_argument("--drive-url", type=str, help="URL ou ID de uma pasta do Google Drive")
        parser.add_argument("--no-drive", action="store_true", help="Desativa indexação do Google Drive")

    def handle(self, *args, **options):
        local_dir = options.get("local_dir")
        drive_url = options.get("drive_url")
        no_drive = options.get("no_drive", False)

        self.stdout.write("Iniciando indexação de arquivos...")
        indexer = IndexerService()

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        stats = loop.run_until_complete(
            indexer.aindex_directory_and_drive(
                local_dir=local_dir,
                include_drive=not no_drive,
                drive_url=drive_url
            )
        )

        self.stdout.write(self.style.SUCCESS(
            f"Indexação concluída! Total arquivos: {stats.get('total_files', 0)} "
            f"(Indexados: {stats.get('indexed_files', 0)}, Erros: {stats.get('error_files', 0)}, "
            f"Total trechos/chunks: {stats.get('total_chunks', 0)})"
        ))
