from datetime import datetime
from typing import Dict, List

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from .models import Emotion, EmotionAnalysis, WeightedEmotionResult


class EmotionAnalyzer:
    def __init__(self, model_name: str = "circulus/koelectra-emotion-v1"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # Map model output indices to emotions
        self.idx_to_emotion = {
            0: Emotion.JOY,
            1: Emotion.SADNESS,
            2: Emotion.ANGER,
            3: Emotion.FEAR,
            4: Emotion.SURPRISE,
            5: Emotion.DISGUST,
            6: Emotion.NEUTRAL,
        }

    def calculate_time_weight(
        self, entry_date: datetime, latest_date: datetime
    ) -> float:
        """
        Calculate weight based on how recent the entry is.
        More recent entries get higher weights.

        Args:
            entry_date: The date of the entry
            latest_date: The date of the most recent entry

        Returns:
            float: Weight between 0.2 and 1.0, never goes below 0.2
        """
        days_diff = (latest_date - entry_date).days
        # Ensure days_diff is non-negative
        days_diff = max(0, days_diff)

        # Calculate weight with 0.15 decay per day, minimum 0.1
        decay_rate = 0.15
        weight = max(0.1, 1.0 - (days_diff * decay_rate))

        return weight

    def analyze_single(self, text: str) -> EmotionAnalysis:
        """Analyze emotion for a single text entry"""
        if not text.strip():
            raise ValueError("Empty text cannot be analyzed")

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
            prediction = torch.argmax(probs, dim=1)
            confidence = float(probs[0][prediction])

        emotion = self.idx_to_emotion[prediction.item()]
        return EmotionAnalysis(emotion=emotion, confidence=confidence)

    def analyze_weighted(
        self, entries: List[Dict[str, str | datetime]]
    ) -> EmotionAnalysis:
        """
        Analyze emotions with time-based weighting

        Args:
            entries: List of dicts containing 'content' and 'date' keys

        Returns:
            EmotionAnalysis for the weighted result
        """
        if not entries:
            raise ValueError("No entries provided for analysis")

        # Sort entries by date (newest first)
        sorted_entries = sorted(entries, key=lambda x: x["date"], reverse=True)
        latest_date = sorted_entries[0]["date"]

        # Analyze each entry with weights
        weighted_results: List[WeightedEmotionResult] = []

        for entry in sorted_entries:
            # Analyze the entry
            analysis = self.analyze_single(entry["content"])

            # Calculate time-based weight
            weight = self.calculate_time_weight(entry["date"], latest_date)

            weighted_results.append(
                WeightedEmotionResult(
                    emotion=analysis.emotion,
                    confidence=analysis.confidence,
                    weight=weight,
                )
            )

        # Aggregate emotions with weights
        emotion_scores: Dict[Emotion, float] = {emotion: 0.0 for emotion in Emotion}
        total_weight = 0.0

        for result in weighted_results:
            score = result.confidence * result.weight
            emotion_scores[result.emotion] += score
            total_weight += result.weight

        # Normalize scores and find the dominant emotion
        if total_weight > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] /= total_weight

        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])

        return EmotionAnalysis(
            emotion=dominant_emotion[0], confidence=dominant_emotion[1]
        )
