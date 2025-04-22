from unittest.mock import patch

import pytest
import requests

from diary_emotion_action.github_updater import GitHubStatusUpdater
from diary_emotion_action.models import GitHubStatus


@pytest.fixture
def github_updater():
    return GitHubStatusUpdater("fake-token")


def test_update_status_success(github_updater):
    status = GitHubStatus(emoji="😄", message="Test status")

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        result = github_updater.update_status(status)
        assert result is True


def test_update_status_failure(github_updater):
    status = GitHubStatus(emoji="😄", message="Test status")

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 401
        result = github_updater.update_status(status)
        assert result is False
