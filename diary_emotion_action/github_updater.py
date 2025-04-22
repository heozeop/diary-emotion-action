import httpx
from typing import Optional

from .models import GitHubStatus


class GitHubStatusUpdater:
    def __init__(self, token: str):
        self.token = token
        self.api_url = "https://api.github.com/graphql"

    async def update_status(self, status: GitHubStatus) -> bool:
        """
        Update GitHub user status asynchronously.

        Args:
            status: GitHubStatus containing emoji and message

        Returns:
            bool indicating success
        """
        query = """
        mutation ChangeUserStatus($emoji: String!, $message: String!) {
          changeUserStatus(input: {emoji: $emoji, message: $message}) {
            status {
              emoji
              message
            }
          }
        }
        """

        variables = {
            "emoji": status.emoji,
            "message": status.message,
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                json={"query": query, "variables": variables},
                headers=headers,
            )

        return response.status_code == 200
