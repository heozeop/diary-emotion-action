import pytest
import torch
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from notion_mood_2_git_status.emotion_analyzer import EmotionAnalyzer
from notion_mood_2_git_status.models import Emotion
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from diary_emotion_action.emotion_analyzer import EmotionAnalyzer as NewEmotionAnalyzer
from diary_emotion_action.models import (
    Emotion as NewEmotion,
    EmotionAnalysis,
    WeightedEmotionResult,
)


@pytest.fixture
def mock_tokenizer():
    tokenizer = Mock(spec=AutoTokenizer)
    tokenizer.return_value = {
        "input_ids": torch.tensor([[1, 2, 3]]),
        "attention_mask": torch.tensor([[1, 1, 1]]),
    }
    return tokenizer


@pytest.fixture
def mock_model():
    model = Mock(spec=AutoModelForSequenceClassification)
    # Create mock output that simulates model prediction
    model_output = Mock()
    # Create a tensor that would give different emotions based on input
    model_output.logits = torch.tensor(
        [[2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]]
    )  # Bias towards JOY (index 0)
    model.return_value = model_output
    return model


@pytest.fixture
def emotion_analyzer(mock_tokenizer, mock_model):
    with (
        patch(
            "diary_emotion_action.emotion_analyzer.AutoTokenizer.from_pretrained",
            return_value=mock_tokenizer,
        ),
        patch(
            "diary_emotion_action.emotion_analyzer.AutoModelForSequenceClassification.from_pretrained",
            return_value=mock_model,
        ),
    ):
        analyzer = NewEmotionAnalyzer()
        return analyzer


class TestEmotionAnalyzer:
    def test_init(self):
        """Test initialization of EmotionAnalyzer"""
        with (
            patch(
                "diary_emotion_action.emotion_analyzer.AutoTokenizer.from_pretrained"
            ) as mock_tokenizer,
            patch(
                "diary_emotion_action.emotion_analyzer.AutoModelForSequenceClassification.from_pretrained"
            ) as mock_model,
        ):

            analyzer = NewEmotionAnalyzer()

            assert mock_tokenizer.called
            assert mock_model.called
            assert len(analyzer.idx_to_emotion) == 7
            assert NewEmotion.JOY in analyzer.idx_to_emotion.values()

    def test_analyze_single_valid_text(self, emotion_analyzer):
        """Test emotion analysis for a single valid text entry"""
        text = "오늘은 정말 행복한 하루였다!"
        result = emotion_analyzer.analyze_single(text)

        assert isinstance(result, EmotionAnalysis)
        assert isinstance(result.emotion, NewEmotion)
        assert 0 <= result.confidence <= 1

    def test_analyze_single_empty_text(self, emotion_analyzer):
        """Test emotion analysis with empty text"""
        with pytest.raises(ValueError, match="Empty text cannot be analyzed"):
            emotion_analyzer.analyze_single("")

    def test_analyze_weighted_single_entry(self, emotion_analyzer):
        """Test weighted analysis with a single entry"""
        now = datetime.now()
        entries = [{"content": "행복한 하루!", "date": now}]

        result = emotion_analyzer.analyze_weighted(entries)

        assert isinstance(result, EmotionAnalysis)
        assert isinstance(result.emotion, NewEmotion)
        assert result.confidence == pytest.approx(1.0, rel=1e-5)

    def test_analyze_weighted_multiple_entries(self, emotion_analyzer):
        """Test weighted analysis with multiple entries over different days"""
        now = datetime.now()
        entries = [
            {"content": "너무 행복해!", "date": now},  # Today - Joy
            {
                "content": "화가 난다.",  # Yesterday - Anger
                "date": now - timedelta(days=1),
            },
            {
                "content": "그저 그런 하루.",  # 2 days ago - Neutral
                "date": now - timedelta(days=2),
            },
        ]

        result = emotion_analyzer.analyze_weighted(entries)

        assert isinstance(result, EmotionAnalysis)
        # Most recent entry (Joy) should have highest weight
        assert result.emotion == NewEmotion.JOY
        assert 0 <= result.confidence <= 1

    def test_analyze_weighted_empty_entries(self, emotion_analyzer):
        """Test weighted analysis with empty entry list"""
        with pytest.raises(ValueError, match="No entries provided for analysis"):
            emotion_analyzer.analyze_weighted([])

    def test_analyze_weighted_same_day_entries(self, emotion_analyzer):
        """Test weighted analysis with multiple entries from the same day"""
        now = datetime.now()
        entries = [
            {"content": "아침: 기분 좋아!", "date": now},
            {"content": "점심: 피곤하다.", "date": now},
        ]

        result = emotion_analyzer.analyze_weighted(entries)

        assert isinstance(result, EmotionAnalysis)
        assert 0 <= result.confidence <= 1

    def test_analyze_weighted_far_apart_dates(self, emotion_analyzer):
        """Test weighted analysis with entries that are far apart in time"""
        now = datetime.now()
        entries = [
            {"content": "오늘은 좋은 날!", "date": now},
            {
                "content": "옛날 일기",
                "date": now - timedelta(days=30),  # Entry from 30 days ago
            },
        ]

        result = emotion_analyzer.analyze_weighted(entries)

        assert isinstance(result, EmotionAnalysis)
        # Recent entry should heavily outweigh old entry
        assert result.emotion == NewEmotion.JOY

    @pytest.mark.parametrize(
        "content,expected_emotion",
        [
            ("너무 행복해!", NewEmotion.JOY),
            ("너무 슬퍼...", NewEmotion.SADNESS),
            ("화가 난다!", NewEmotion.ANGER),
            ("무서워...", NewEmotion.FEAR),
            ("놀랍다!", NewEmotion.SURPRISE),
            ("역겹다.", NewEmotion.DISGUST),
            ("그냥 그래.", NewEmotion.NEUTRAL),
        ],
    )
    def test_analyze_single_different_emotions(
        self, emotion_analyzer, content, expected_emotion
    ):
        """Test emotion analysis with different types of emotional content"""
        # We need to modify the mock model's output for each emotion
        idx = list(emotion_analyzer.idx_to_emotion.values()).index(expected_emotion)
        logits = torch.zeros(1, 7)
        logits[0][idx] = 2.0  # Make the target emotion dominant

        with patch.object(emotion_analyzer.model, "forward") as mock_forward:
            mock_output = Mock()
            mock_output.logits = logits
            mock_forward.return_value = mock_output

            result = emotion_analyzer.analyze_single(content)

            assert result.emotion == expected_emotion
            assert result.confidence > 0.5

    def test_weight_calculation_consistency(self, emotion_analyzer):
        """Test that weight calculation is consistent and decreasing with time"""
        now = datetime.now()
        dates = [now - timedelta(days=i) for i in range(5)]
        weights = [emotion_analyzer.calculate_time_weight(date, now) for date in dates]

        # Weights should be decreasing
        assert all(weights[i] >= weights[i + 1] for i in range(len(weights) - 1))
        # Today's weight should be 1.0
        assert weights[0] == pytest.approx(1.0)
        # Oldest entry should have minimum weight
        assert weights[-1] >= 0.2


def test_analyze_text(emotion_analyzer):
    text = "오늘은 정말 행복한 하루였다!"
    result = emotion_analyzer.analyze(text)

    assert isinstance(result.emotion, NewEmotion)
    assert 0 <= result.confidence <= 1


def test_analyze_empty_text(emotion_analyzer):
    with pytest.raises(ValueError):
        emotion_analyzer.analyze("")


def test_weighted_analysis(emotion_analyzer):
    # Create test entries over the last 5 days
    now = datetime.now()
    test_entries = [
        {"content": "오늘은 정말 행복한 하루였다!", "date": now},  # Today - Joy
        {
            "content": "너무 화가난다.",  # Yesterday - Anger
            "date": now - timedelta(days=1),
        },
        {
            "content": "평범한 하루.",  # 2 days ago - Neutral
            "date": now - timedelta(days=2),
        },
    ]

    result = emotion_analyzer.analyze_weighted(test_entries)

    assert isinstance(result.emotion, NewEmotion)
    assert 0 <= result.confidence <= 1
    # Recent happy entry should have more weight
    assert result.emotion == NewEmotion.JOY


def test_weighted_analysis_empty_entries(emotion_analyzer):
    with pytest.raises(ValueError):
        emotion_analyzer.analyze_weighted([])
