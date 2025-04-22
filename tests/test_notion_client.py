from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from notion_mood_2_git_status.models import DiaryEntry
from notion_mood_2_git_status.notion_client import NotionDiaryClient


@pytest.fixture
def mock_notion_response():
    return {
        "results": [
            {
                "id": "page1",
                "properties": {
                    "Content": {"rich_text": [{"plain_text": "Test diary entry"}]},
                    "Date": {"date": {"start": "2024-02-28T00:00:00Z"}},
                },
            }
        ]
    }


@pytest.fixture
def notion_client():
    return NotionDiaryClient("fake-token", "fake-db-id")


async def test_get_recent_entries(notion_client, mock_notion_response):
    with patch("notion_client.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.databases.query.return_value = mock_notion_response
        MockClient.return_value = mock_client

        entries = await notion_client.get_recent_entries(limit=1)

        assert len(entries) == 1
        assert isinstance(entries[0], DiaryEntry)
        assert entries[0].content == "Test diary entry"
        assert entries[0].date == datetime.fromisoformat("2024-02-28T00:00:00Z")
