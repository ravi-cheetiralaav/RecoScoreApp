"""Facebook Graph API ingestion adapter.

NOTE: Requires a valid Facebook Page Access Token with 'pages_read_engagement' permission.
This adapter is a compliant integration using the official Facebook Graph API.
Do NOT use unofficial scraping in production.
"""
import logging
from datetime import datetime
from typing import List, Optional

import httpx

from app.adapters.base_adapter import BaseIngestionAdapter, RawPost

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class FacebookIngestionAdapter(BaseIngestionAdapter):
    """Ingestion adapter using the official Facebook Graph API."""

    def __init__(self, page_id: str, access_token: str):
        self.page_id = page_id
        self.access_token = access_token

    def get_source_name(self) -> str:
        return "facebook"

    async def fetch_posts(self, since: Optional[datetime] = None, limit: int = 50) -> List[RawPost]:
        """Fetch posts from a Facebook Page using the Graph API."""
        if not self.access_token:
            logger.warning("No Facebook access token configured; returning empty list.")
            return []

        params = {
            "fields": "id,message,created_time,permalink_url",
            "limit": min(limit, 100),
            "access_token": self.access_token,
        }
        if since:
            params["since"] = int(since.timestamp())

        url = f"{GRAPH_API_BASE}/{self.page_id}/posts"
        results: List[RawPost] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            while url:
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPStatusError as e:
                    logger.error(f"Facebook API error: {e.response.status_code} - {e.response.text}")
                    break
                except Exception as e:
                    logger.error(f"Error fetching Facebook posts: {e}")
                    break

                for post in data.get("data", []):
                    message = post.get("message", "")
                    if not message:
                        continue
                    posted_at = datetime.fromisoformat(
                        post["created_time"].replace("Z", "+00:00")
                    )
                    results.append(
                        RawPost(
                            external_id=post["id"],
                            raw_text=message,
                            posted_at=posted_at,
                            post_url=post.get("permalink_url"),
                            source="facebook",
                        )
                    )

                # Handle pagination
                paging = data.get("paging", {})
                next_url = paging.get("next")
                if next_url and len(results) < limit:
                    url = next_url
                    params = {}  # next_url already has params
                else:
                    break

        return results[:limit]
