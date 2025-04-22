import pytest
import torch
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from diary_emotion_action.emotion_analyzer import EmotionAnalyzer
from diary_emotion_action.models import (
    Emotion,
    EmotionAnalysis,
    WeightedEmotionResult,
)
from transformers import AutoModelForSequenceClassification, AutoTokenizer


@pytest.fixture
def mock_tokenizer():
    tokenizer = Mock(spec=AutoTokenizer)
    
    def mock_call(*args, **kwargs):
        # Create a mock that simulates the tokenizer output with a to() method
        data = {
            "input_ids": torch.tensor([[1, 2, 3]]).to("cpu"),
            "attention_mask": torch.tensor([[1, 1, 1]]).to("cpu"),
        }

        output = MagicMock()
        output.__getitem__.side_effect = data.__getitem__
        output.keys.side_effect = data.keys
        output.values.side_effect = data.values
        output.to.side_effect = lambda *args, **kwargs: {k: v.to(*args, **kwargs) for k, v in data.items()}

        return output

    tokenizer.side_effect = mock_call
    return tokenizer


@pytest.fixture
def mock_model():
    model = Mock(spec=AutoModelForSequenceClassification)
    model.logits = torch.tensor([[2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]]).to("cpu")
    
    def mock_to(*args, **kwargs):
        return model

    def mock_call(*args, **kwargs):
        return model
    
    model.to = mock_to
    model.side_effect = mock_call
    return model


@pytest.fixture
def emotion_analyzer(mock_tokenizer, mock_model):
    with patch(
        "diary_emotion_action.emotion_analyzer.AutoTokenizer.from_pretrained",
        return_value=mock_tokenizer,
    ), patch(
        "diary_emotion_action.emotion_analyzer.AutoModelForSequenceClassification.from_pretrained",
        return_value=mock_model,
    ), patch(
        "diary_emotion_action.emotion_analyzer.torch.device",
        return_value="cpu"
    ):
        analyzer = EmotionAnalyzer()
        return analyzer


class TestEmotionAnalyzer:
    def test_init(self):
        """Test initialization of EmotionAnalyzer"""
        with patch(
            "diary_emotion_action.emotion_analyzer.AutoTokenizer.from_pretrained"
        ) as mock_tokenizer, patch(
            "diary_emotion_action.emotion_analyzer.AutoModelForSequenceClassification.from_pretrained"
        ) as mock_model, patch(
            "diary_emotion_action.emotion_analyzer.torch.device",
            return_value="cpu"
        ):
            analyzer = EmotionAnalyzer()

            assert mock_tokenizer.called
            assert mock_model.called
            assert len(analyzer.idx_to_emotion) == 7
            assert Emotion.JOY in analyzer.idx_to_emotion.values()

    def test_analyze_single_valid_text(self, emotion_analyzer):
        """Test emotion analysis for a single valid text entry"""
        text = "오늘은 정말 행복한 하루였다!"
        result = emotion_analyzer.analyze_single(text)

        assert isinstance(result, EmotionAnalysis)
        assert isinstance(result.emotion, Emotion)
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
        assert isinstance(result.emotion, Emotion)

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
        assert result.emotion == Emotion.JOY
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
        assert result.emotion == Emotion.JOY

    @pytest.mark.parametrize(
        "content,expected_emotion",
        [
            ("너무 행복해!", Emotion.JOY),
            ("너무 슬퍼...", Emotion.SADNESS),
            ("화가 난다!", Emotion.ANGER),
            ("무서워...", Emotion.FEAR),
            ("놀랍다!", Emotion.SURPRISE),
            ("역겹다.", Emotion.DISGUST),
            ("그냥 그래.", Emotion.NEUTRAL),
        ],
    )
    def test_analyze_single_different_emotions(
        self, emotion_analyzer, content, expected_emotion
    ):
        """Test emotion analysis with different types of emotional content"""
        # Create mock output for the specific emotion
        idx = list(emotion_analyzer.idx_to_emotion.values()).index(expected_emotion)
        logits = torch.zeros(1, 7)
        logits[0][idx] = 2.0  # Make the target emotion dominant

        # Create a mock output object
        mock_output = MagicMock()
        mock_output.logits = logits

        # Mock the model's __call__ method
        emotion_analyzer.model = MagicMock()
        emotion_analyzer.model.return_value = mock_output
        emotion_analyzer.model.to.return_value = emotion_analyzer.model  # Handle model.to() calls

        result = emotion_analyzer.analyze_single(content)

        assert result.emotion == expected_emotion
        assert result.confidence > 0.5
        
        # Verify the model was called
        emotion_analyzer.model.assert_called_once()

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
        assert weights[-1] >= 0.1

    def test_analyze_text(self, emotion_analyzer):
        text = "오늘은 정말 행복한 하루였다!"
        result = emotion_analyzer.analyze_single(text)

        assert isinstance(result.emotion, Emotion)
        assert 0 <= result.confidence <= 1


    def test_analyze_empty_text(self, emotion_analyzer):
        with pytest.raises(ValueError):
            emotion_analyzer.analyze_single("")


    def test_weighted_analysis(self, emotion_analyzer):
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

        assert isinstance(result.emotion, Emotion)
        assert 0 <= result.confidence <= 1
        # Recent happy entry should have more weight
        assert result.emotion == Emotion.JOY


    def test_weighted_analysis_empty_entries(self, emotion_analyzer):
        with pytest.raises(ValueError):
            emotion_analyzer.analyze_weighted([])
