import asyncio
import os
from typing import List, Optional

from dotenv import load_dotenv

from .emotion_analyzer import EmotionAnalyzer
from .github_updater import GitHubStatusUpdater
from .models import EMOTION_TO_STATUS, DiaryEntry, EmotionAnalysis, GitHubStatus
from .notion_client import NotionDiaryClient


class DiaryEmotionAction:
    def __init__(
        self,
        notion_token: str,
        notion_database_id: str,
        github_token: str,
        model_name: str = "circulus/koelectra-emotion-v1",
        entries_limit: int = 10,
    ):
        self.notion_client = NotionDiaryClient(notion_token, notion_database_id)
        self.emotion_analyzer = EmotionAnalyzer(model_name)
        self.github_updater = GitHubStatusUpdater(github_token)
        self.entries_limit = entries_limit

    async def run(self) -> bool:
        """
        Run the complete workflow

        Returns:
            bool indicating success
        """
        # Get recent entries
        entries = await self.notion_client.get_recent_entries(self.entries_limit)
        if not entries:
            return False

        # Prepare entries for analysis
        entries_for_analysis = [
            {"content": entry.content, "date": entry.date} for entry in entries
        ]

        # Analyze entries with time-based weighting
        analysis = self.emotion_analyzer.analyze_weighted(entries_for_analysis)

        # Update GitHub status
        status = EMOTION_TO_STATUS[analysis.emotion]
        return self.github_updater.update_status(status)


async def main():
    load_dotenv()

    required_env_vars = [
        "NOTION_TOKEN",
        "NOTION_DATABASE_ID",
        "GITHUB_TOKEN",
    ]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")

    action = DiaryEmotionAction(
        notion_token=os.getenv("NOTION_TOKEN"),
        notion_database_id=os.getenv("NOTION_DATABASE_ID"),
        github_token=os.getenv("GITHUB_TOKEN"),
        entries_limit=10,  # Analyze last 10 entries
    )

    success = await action.run()
    if not success:
        raise RuntimeError("Failed to update GitHub status")


if __name__ == "__main__":
    asyncio.run(main())
