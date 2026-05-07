"""Ingestion Agent - pulls posts from the configured source adapter and persists them."""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.adapters.base_adapter import BaseIngestionAdapter
from app.adapters.mock_adapter import MockIngestionAdapter
from app.adapters.facebook_adapter import FacebookIngestionAdapter
from app.config import get_settings
from app.models.source_post import SourcePost

logger = logging.getLogger(__name__)


def get_adapter(settings=None) -> BaseIngestionAdapter:
    """Factory: return the configured ingestion adapter."""
    if settings is None:
        settings = get_settings()
    if settings.ingestion_adapter == "facebook" and settings.facebook_access_token:
        return FacebookIngestionAdapter(
            page_id=settings.facebook_page_id,
            access_token=settings.facebook_access_token,
        )
    return MockIngestionAdapter()


class IngestionAgent:
    """
    Ingestion Agent: Fetches posts from the source adapter and stores them in the DB.
    Implements idempotent ingestion (no duplicate external_id).
    """

    def __init__(self, db: Session, adapter: Optional[BaseIngestionAdapter] = None):
        self.db = db
        self.adapter = adapter or get_adapter()

    async def run(self, since: Optional[datetime] = None, limit: int = 50) -> dict:
        """
        Fetch posts from the adapter and persist new ones.

        Returns:
            dict with keys: fetched, new, skipped
        """
        logger.info(f"IngestionAgent: fetching posts (since={since}, limit={limit})")
        raw_posts = await self.adapter.fetch_posts(since=since, limit=limit)

        fetched = len(raw_posts)
        new_count = 0
        skipped_count = 0

        for post in raw_posts:
            # Idempotency: skip if already ingested
            existing = (
                self.db.query(SourcePost)
                .filter(SourcePost.external_id == post.external_id)
                .first()
            )
            if existing:
                skipped_count += 1
                continue

            db_post = SourcePost(
                external_id=post.external_id,
                source=post.source,
                raw_text=post.raw_text,
                post_url=post.post_url,
                posted_at=post.posted_at,
                ingested_at=datetime.utcnow(),
                is_processed=False,
            )
            self.db.add(db_post)
            new_count += 1

        self.db.commit()
        logger.info(f"IngestionAgent: fetched={fetched}, new={new_count}, skipped={skipped_count}")
        return {"fetched": fetched, "new": new_count, "skipped": skipped_count}
