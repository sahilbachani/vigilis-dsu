"""
Main Text Analyzer Module
Orchestrates text analysis using multiple ML models.
Computes hate_score, extremism_score, misinformation_score, emotion_scores, and flagged status.
"""

import logging
import asyncio
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import numpy as np

from .models_loader import ModelsLoader
from .text_processor import TextProcessor
from .config import (
    FLAGGING_THRESHOLDS,
    MIN_CONFIDENCE_THRESHOLD,
    EMOTION_LABELS,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    text: str
    hate_score: float = 0.0
    extremism_score: float = 0.0
    misinformation_score: float = 0.0
    emotion_anger: float = 0.0
    emotion_fear: float = 0.0
    emotion_disgust: float = 0.0
    emotion_neutral: float = 1.0
    confidence_score: float = 0.0
    flagged: bool = False
    flags_triggered: List[str] = None
    analysis_timestamp: datetime = None
    processing_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.flags_triggered is None:
            self.flags_triggered = []
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        result_dict = asdict(self)
        result_dict['analysis_timestamp'] = self.analysis_timestamp
        return result_dict


class TextAnalyzer:
    """
    Main text analyzer that orchestrates inference across multiple models.
    Handles async processing and concurrent analysis of multiple posts.
    """
    
    def __init__(self, models_loader: Optional[ModelsLoader] = None):
        """
        Initialize the analyzer.
        
        Args:
            models_loader: Optional pre-initialized ModelsLoader instance
        """
        self.models_loader = models_loader or ModelsLoader.create_singleton()
        self.text_processor = TextProcessor()
        self._semaphore = asyncio.Semaphore(4)  # Max concurrent analyses
    
    async def analyze_text_async(self, text: str) -> AnalysisResult:
        """
        Asynchronously analyze text.
        Useful for non-blocking processing when handling multiple posts.
        
        Args:
            text: Raw text to analyze
            
        Returns:
            AnalysisResult with all computed scores
        """
        async with self._semaphore:
            return await asyncio.to_thread(self.analyze_text, text)
    
    def analyze_text(self, text: str) -> AnalysisResult:
        """
        Analyze text and compute all scores.
        
        Args:
            text: Raw text to analyze
            
        Returns:
            AnalysisResult with computed scores
        """
        import time
        start_time = time.time()
        
        # Validate and preprocess
        is_valid, reason = self.text_processor.validate_text(text)
        if not is_valid:
            logger.warning(f"Invalid text: {reason}")
            return AnalysisResult(text=text)
        
        # Clean text for analysis
        cleaned_text = self.text_processor.preprocess_for_inference(text)
        if not cleaned_text:
            return AnalysisResult(text=text)
        
        # Initialize result
        result = AnalysisResult(text=text)
        
        # Run inferences
        hate_score, hate_conf = self._analyze_hate_speech(cleaned_text)
        result.hate_score = hate_score
        
        extremism_score, extremism_conf = self._analyze_extremism(cleaned_text)
        result.extremism_score = extremism_score
        
        misinformation_score, misinformation_conf = self._analyze_misinformation(cleaned_text)
        result.misinformation_score = misinformation_score
        
        emotion_dict, emotion_conf = self._analyze_emotions(cleaned_text)
        result.emotion_anger = emotion_dict.get('emotion_anger', 0.0)
        result.emotion_fear = emotion_dict.get('emotion_fear', 0.0)
        result.emotion_disgust = emotion_dict.get('emotion_disgust', 0.0)
        result.emotion_neutral = emotion_dict.get('emotion_neutral', 1.0)
        
        # Compute overall confidence
        result.confidence_score = self._compute_confidence(
            hate_conf, extremism_conf, misinformation_conf, emotion_conf
        )
        
        # Determine if flagged
        result.flagged, result.flags_triggered = self._determine_flagged(result)
        
        # Record processing time
        result.processing_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _analyze_hate_speech(self, text: str) -> Tuple[float, float]:
        """
        Analyze hate speech using transformer model.
        
        Returns:
            Tuple of (hate_score, confidence)
        """
        try:
            model = self.models_loader.get_model("hate_speech_detection")
            if not model:
                return 0.0, 0.0
            
            results = model(text, truncation=True)
            
            if not results:
                return 0.0, 0.0
            
            # results is a list of dicts with 'label' and 'score'
            top_result = results[0]
            label = top_result.get('label', '').lower()
            score = top_result.get('score', 0.0)
            
            # Map label to hate score
            if 'hate' in label or 'offensive' in label:
                hate_score = score
            else:
                hate_score = 1.0 - score  # Invert if "neither"
            
            return min(hate_score, 1.0), score
            
        except Exception as e:
            logger.error(f"Error in hate speech analysis: {str(e)}")
            return 0.0, 0.0
    
    def _analyze_extremism(self, text: str) -> Tuple[float, float]:
        """
        Analyze extremism using multilingual RoBERTa model.
        
        Returns:
            Tuple of (extremism_score, confidence)
        """
        try:
            model = self.models_loader.get_model("extremism_detection")
            if not model:
                return 0.0, 0.0
            
            results = model(text, truncation=True)
            
            if not results:
                return 0.0, 0.0
            
            # Get the highest scoring label indicating extremism
            top_result = results[0]
            label = top_result.get('label', '').lower()
            score = top_result.get('score', 0.0)
            
            # XLM-RoBERTa gives normalized scores
            # Higher score on negative/extremist label = higher extremism
            if any(x in label for x in ['extreme', 'violent', 'radical']):
                extremism_score = score
            else:
                extremism_score = 1.0 - score
            
            return min(extremism_score, 1.0), score
            
        except Exception as e:
            logger.error(f"Error in extremism analysis: {str(e)}")
            return 0.0, 0.0
    
    def _analyze_misinformation(self, text: str) -> Tuple[float, float]:
        """
        Analyze misinformation using RoBERTa detector.
        
        Returns:
            Tuple of (misinformation_score, confidence)
        """
        try:
            model = self.models_loader.get_model("misinformation_detection")
            if not model:
                return 0.0, 0.0
            
            results = model(text, truncation=True)
            
            if not results:
                return 0.0, 0.0
            
            # Get confidence for "fake" label
            top_result = results[0]
            label = top_result.get('label', '').lower()
            score = top_result.get('score', 0.0)
            
            # Higher score on "Fake" or "generated" = higher misinformation
            if 'fake' in label or 'generated' in label:
                misinformation_score = score
            else:
                misinformation_score = 1.0 - score
            
            return min(misinformation_score, 1.0), score
            
        except Exception as e:
            logger.error(f"Error in misinformation analysis: {str(e)}")
            return 0.0, 0.0
    
    def _analyze_emotions(self, text: str) -> Tuple[Dict[str, float], float]:
        """
        Analyze emotional intensity.
        
        Returns:
            Tuple of (emotion_dict, confidence)
        """
        try:
            model = self.models_loader.get_model("emotion_detection")
            if not model:
                return {}, 0.0
            
            results = model(text, truncation=True)
            
            if not results:
                return {}, 0.0
            
            # DistilBERT emotion model returns top-1 prediction
            emotion_dict = {
                'emotion_anger': 0.0,
                'emotion_fear': 0.0,
                'emotion_disgust': 0.0,
                'emotion_neutral': 0.0,
            }
            
            confidence = 0.0
            
            if isinstance(results, list) and results:
                # If results is a list of dicts with label and score
                for item in results:
                    label = item.get('label', '').lower()
                    score = item.get('score', 0.0)
                    
                    if 'anger' in label:
                        emotion_dict['emotion_anger'] = score
                    elif 'fear' in label:
                        emotion_dict['emotion_fear'] = score
                    elif 'disgust' in label:
                        emotion_dict['emotion_disgust'] = score
                    elif 'neutral' in label or 'joy' in label or 'sadness' in label:
                        emotion_dict['emotion_neutral'] = score
                    
                    confidence = max(confidence, score)
            
            # Ensure all keys exist
            for key in ['emotion_anger', 'emotion_fear', 'emotion_disgust', 'emotion_neutral']:
                if key not in emotion_dict:
                    emotion_dict[key] = 0.0
            
            return emotion_dict, confidence
            
        except Exception as e:
            logger.error(f"Error in emotion analysis: {str(e)}")
            return {}, 0.0
    
    def _compute_confidence(self, hate_conf: float, extremism_conf: float, 
                           misinformation_conf: float, emotion_conf: float) -> float:
        """
        Compute overall confidence score as average of model confidences.
        """
        confidences = [
            hate_conf,
            extremism_conf,
            misinformation_conf,
            emotion_conf
        ]
        # Filter out zero confidences (failed models)
        valid_confidences = [c for c in confidences if c > 0]
        
        if not valid_confidences:
            return 0.0
        
        return np.mean(valid_confidences)
    
    def _determine_flagged(self, result: AnalysisResult) -> Tuple[bool, List[str]]:
        """
        Determine if post should be flagged based on thresholds.
        
        Returns:
            Tuple of (is_flagged, list_of_triggered_flags)
        """
        flags_triggered = []
        
        # Check each score against thresholds
        if result.hate_score > FLAGGING_THRESHOLDS.get("hate_score", 0.5):
            flags_triggered.append(f"hate_speech(score={result.hate_score:.2f})")
        
        if result.extremism_score > FLAGGING_THRESHOLDS.get("extremism_score", 0.5):
            flags_triggered.append(f"extremism(score={result.extremism_score:.2f})")
        
        if result.misinformation_score > FLAGGING_THRESHOLDS.get("misinformation_score", 0.6):
            flags_triggered.append(f"misinformation(score={result.misinformation_score:.2f})")
        
        if result.emotion_anger > FLAGGING_THRESHOLDS.get("emotion_anger", 0.7):
            flags_triggered.append(f"high_anger(score={result.emotion_anger:.2f})")
        
        if result.emotion_fear > FLAGGING_THRESHOLDS.get("emotion_fear", 0.7):
            flags_triggered.append(f"high_fear(score={result.emotion_fear:.2f})")
        
        if result.emotion_disgust > FLAGGING_THRESHOLDS.get("emotion_disgust", 0.7):
            flags_triggered.append(f"high_disgust(score={result.emotion_disgust:.2f})")
        
        is_flagged = len(flags_triggered) > 0
        
        return is_flagged, flags_triggered
    
    async def analyze_batch_async(self, texts: List[str]) -> List[AnalysisResult]:
        """
        Analyze multiple texts concurrently.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of AnalysisResult objects
        """
        tasks = [self.analyze_text_async(text) for text in texts]
        results = await asyncio.gather(*tasks)
        return results
    
    def analyze_batch(self, texts: List[str]) -> List[AnalysisResult]:
        """
        Analyze multiple texts sequentially.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of AnalysisResult objects
        """
        return [self.analyze_text(text) for text in texts]
