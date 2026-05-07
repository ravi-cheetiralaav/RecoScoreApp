"""Mock ingestion adapter with sample stock recommendation posts."""
import json
import os
from datetime import datetime
from typing import List, Optional

from app.adapters.base_adapter import BaseIngestionAdapter, RawPost


SEED_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "seed_data", "sample_posts.json")


class MockIngestionAdapter(BaseIngestionAdapter):
    """Mock adapter that returns sample posts from a JSON seed file."""

    def __init__(self, seed_file: str = SEED_DATA_PATH):
        self.seed_file = seed_file

    def get_source_name(self) -> str:
        return "mock"

    async def fetch_posts(self, since: Optional[datetime] = None, limit: int = 50) -> List[RawPost]:
        """Load posts from seed JSON file."""
        try:
            with open(self.seed_file, "r", encoding="utf-8") as f:
                posts_data = json.load(f)
        except FileNotFoundError:
            return []

        results = []
        for item in posts_data[:limit]:
            posted_at = datetime.fromisoformat(item["posted_at"])
            if since and posted_at <= since:
                continue
            results.append(
                RawPost(
                    external_id=item["id"],
                    raw_text=item["text"],
                    posted_at=posted_at,
                    post_url=item.get("url"),
                    source="mock",
                    metadata=item.get("metadata"),
                )
            )
        return results
