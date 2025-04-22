from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class Emotion(Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"


@dataclass
class DiaryEntry:
    content: str
    date: datetime
    page_id: str


@dataclass
class EmotionAnalysis:
    emotion: Emotion
    confidence: float


@dataclass
class WeightedEmotionResult:
    emotion: Emotion
    confidence: float
    weight: float


@dataclass
class GitHubStatus:
    emoji: str
    message: str


# Mapping emotions to GitHub status with more nuanced messages
EMOTION_TO_STATUS: Dict[Emotion, GitHubStatus] = {
    Emotion.JOY: GitHubStatus("😄", "Been feeling pretty good lately!"),
    Emotion.SADNESS: GitHubStatus("😢", "Going through some emotions..."),
    Emotion.ANGER: GitHubStatus("😠", "Taking deep breaths"),
    Emotion.FEAR: GitHubStatus("😨", "Dealing with some uncertainty"),
    Emotion.SURPRISE: GitHubStatus("😲", "Life's been full of surprises!"),
    Emotion.DISGUST: GitHubStatus("🤢", "Need a change of pace"),
    Emotion.NEUTRAL: GitHubStatus("😐", "Keeping it steady"),
}
