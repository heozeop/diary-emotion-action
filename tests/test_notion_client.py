from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from notion_client import AsyncClient
from httpx import HTTPStatusError

from diary_emotion_action.models import DiaryEntry
from diary_emotion_action.notion_client import NotionDiaryClient


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
def mock_notion_client():
    async def mock_query(*args, **kwargs):
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

    mock_db = AsyncMock()
    mock_db.query = mock_query

    mock_client = AsyncMock(spec=AsyncClient)
    mock_client.databases = mock_db
    
    return mock_client


@pytest.fixture
def notion_client(mock_notion_client):
    with patch("diary_emotion_action.notion_client.AsyncClient", return_value=mock_notion_client):
        return NotionDiaryClient("fake-token", "fake-db-id")


@pytest.mark.asyncio
async def test_get_recent_entries(notion_client):
    entries = await notion_client.get_recent_entries(limit=1)

    assert len(entries) == 1
    assert isinstance(entries[0], DiaryEntry)
    assert entries[0].content == "Test diary entry"
    assert entries[0].date == datetime.fromisoformat("2024-02-28T00:00:00Z")


@pytest.mark.asyncio
async def test_get_recent_entries_unauthorized():
    """Test handling of unauthorized access"""
    # Create a new client instance for this test
    with patch("diary_emotion_action.notion_client.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_databases = AsyncMock()
        mock_databases.query.side_effect = HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=MagicMock(status_code=401)
        )
        mock_client.databases = mock_databases
        MockClient.return_value = mock_client

        # Create a new NotionDiaryClient instance
        client = NotionDiaryClient("fake-token", "fake-db-id")

        with pytest.raises(HTTPStatusError):
            await client.get_recent_entries(limit=1)
