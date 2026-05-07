"""Base adapter interface for ingestion sources."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class RawPost:
    """Represents a raw post from an ingestion source."""
    external_id: str
    raw_text: str
    posted_at: datetime
    post_url: Optional[str] = None
    source: str = "unknown"
    metadata: Optional[dict] = None


class BaseIngestionAdapter(ABC):
    """Abstract base class for all ingestion adapters."""

    @abstractmethod
    async def fetch_posts(self, since: Optional[datetime] = None, limit: int = 50) -> List[RawPost]:
        """
        Fetch posts from the source.

        Args:
            since: Only fetch posts after this datetime (for incremental ingestion).
            limit: Maximum number of posts to fetch.

        Returns:
            List of RawPost objects.
        """
        ...

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this ingestion source."""
        ...
