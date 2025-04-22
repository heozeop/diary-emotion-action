from datetime import datetime
from typing import List, Optional

from notion_client import Client

from .models import DiaryEntry


class NotionDiaryClient:
    def __init__(self, token: str, database_id: str):
        self.client = Client(auth=token)
        self.database_id = database_id

    async def get_recent_entries(self, limit: int = 5) -> List[DiaryEntry]:
        """
        Fetch recent diary entries from Notion database

        Args:
            limit: Maximum number of entries to fetch

        Returns:
            List of DiaryEntry objects sorted by date (newest first)
        """
        response = self.client.databases.query(
            database_id=self.database_id,
            sorts=[{"property": "Date", "direction": "descending"}],
            page_size=limit,
        )

        entries = []
        for page in response["results"]:
            content = self._extract_content(page)
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

    def _extract_content(self, page: dict) -> Optional[str]:
        """Extract content from Notion page"""
        try:
            return page["properties"]["Content"]["rich_text"][0]["plain_text"]
        except (KeyError, IndexError):
            return None

    def _extract_date(self, page: dict) -> Optional[datetime]:
        """Extract date from Notion page"""
        try:
            date_str = page["properties"]["Date"]["date"]["start"]
            return datetime.fromisoformat(date_str)
        except (KeyError, ValueError):
            return None
