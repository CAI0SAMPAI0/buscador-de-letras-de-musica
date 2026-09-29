from django.db import models
from django.utils import timezone

class IndexedFile(models.Model):
    SOURCE_LOCAL = 'local'
    SOURCE_GOOGLE_DRIVE = 'google_drive'
    SOURCE_CHOICES = [
        (SOURCE_LOCAL, 'Local (HD/USB)'),
        (SOURCE_GOOGLE_DRIVE, 'Google Drive'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_INDEXED = 'indexed'
    STATUS_ERROR = 'error'
    STATUS_REMOVED = 'removed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_INDEXED, 'Indexado'),
        (STATUS_ERROR, 'Erro'),
        (STATUS_REMOVED, 'Removido'),
    ]

    file_name = models.CharField(max_length=255)
    extension = models.CharField(max_length=20)
    file_path = models.TextField(unique=True)
    folder_name = models.CharField(max_length=255)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_LOCAL)
    external_id = models.CharField(max_length=255, blank=True, null=True)
    file_hash = models.CharField(max_length=64, blank=True, null=True)
    file_size = models.BigIntegerField(default=0)
    modified_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    last_indexed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Arquivo Indexado"
        verbose_name_plural = "Arquivos Indexados"
        indexes = [
            models.Index(fields=['source', 'status']),
            models.Index(fields=['file_hash']),
            models.Index(fields=['extension']),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.source}) - {self.status}"


class DocumentChunk(models.Model):
    indexed_file = models.ForeignKey(
        IndexedFile,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    page_number = models.IntegerField(blank=True, null=True)
    slide_number = models.IntegerField(blank=True, null=True)
    snippet_text = models.TextField()
    normalized_text = models.TextField(db_index=True)
    chunk_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Trecho do Documento"
        verbose_name_plural = "Trechos dos Documentos"
        indexes = [
            models.Index(fields=['indexed_file', 'page_number']),
            models.Index(fields=['indexed_file', 'slide_number']),
        ]

    def __str__(self):
        loc = ""
        if self.page_number is not None:
            loc = f" (Pág. {self.page_number})"
        elif self.slide_number is not None:
            loc = f" (Slide {self.slide_number})"
        return f"{self.indexed_file.file_name}{loc}: {self.snippet_text[:50]}..."
