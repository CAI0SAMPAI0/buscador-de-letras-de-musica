# Async background tasks helper for local background processing without Celery/Redis
import logging
import asyncio

logger = logging.getLogger(__name__)

async def run_indexing_task(local_dir=None, include_drive=True):
    from .services import IndexerService
    indexer = IndexerService()
    try:
        stats = await indexer.aindex_directory_and_drive(local_dir=local_dir, include_drive=include_drive)
        logger.info(f"Background indexing completed: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error in background indexing task: {e}")
        raise
