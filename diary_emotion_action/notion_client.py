from datetime import datetime
from typing import List, Optional

from notion_client import AsyncClient
import logging
from .models import DiaryEntry


class NotionDiaryClient:
    def __init__(self, token: str, database_id: str):
        self.client = AsyncClient(auth=token)
        self.database_id = database_id

    async def get_recent_entries(self, limit: int = 5) -> List[DiaryEntry]:
        """
        Fetch recent diary entries from Notion database

        Args:
            limit: Maximum number of entries to fetch

        Returns:
            List of DiaryEntry objects sorted by date (newest first)
        """
        response = await self.client.databases.query(
            database_id=self.database_id,
            sorts=[{"property": "Date", "direction": "descending"}],
            page_size=limit,
        )

        entries = []
        for page in response["results"]:
            content = await self._extract_content(page)
            date = self._extract_date(page)
            if content and date:
                entries.append(
                    DiaryEntry(
                        content=content,
                        date=date,
                        page_id=page["id"],
                    )
                )

        return entries

    async def _extract_content(self, page: dict) -> Optional[str]:
        """Extract content from Notion page"""
        try:
            response = await self.client.blocks.children.list(block_id=page["id"])
            contents = []
            for block in response["results"]:
                if block["type"] == "paragraph":
                    contents.append(block["paragraph"]["rich_text"][0]["plain_text"])
            return "\n".join(contents)
        except (KeyError, IndexError):
            return None

    def _extract_date(self, page: dict) -> Optional[datetime]:
        """Extract date from Notion page"""
        try:
            date_str = page["properties"]["작성일"]["date"]["start"]
            return datetime.fromisoformat(date_str)
        except (KeyError, ValueError):
            return None
