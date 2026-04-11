"""
Text Preprocessing and Cleaning Module
Handles text normalization, URL removal, mention removal, and whitespace normalization
"""

import re
from typing import Tuple
from .config import MAX_TEXT_LENGTH, MIN_TEXT_LENGTH


class TextProcessor:
    """
    Cleans and preprocesses text for ML model inference.
    Supports English, Urdu, and mixed language text.
    """
    
    # URL pattern
    URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')
    
    # Mention pattern (Twitter/X style)
    MENTION_PATTERN = re.compile(r'@[\w]+')
    
    # Hashtag pattern
    HASHTAG_PATTERN = re.compile(r'#[\w]+')
    
    # Multiple whitespace pattern
    WHITESPACE_PATTERN = re.compile(r'\s+')
    
    # Special characters (but keep Urdu characters)
    SPECIAL_CHAR_PATTERN = re.compile(r'[^\w\s\u0600-\u06FF\-\.!?]')
    
    @staticmethod
    def remove_urls(text: str) -> str:
        """Remove URLs and web addresses from text"""
        return TextProcessor.URL_PATTERN.sub('', text)
    
    @staticmethod
    def remove_mentions(text: str) -> str:
        """Remove Twitter mentions (@username) from text"""
        return TextProcessor.MENTION_PATTERN.sub('', text)
    
    @staticmethod
    def remove_hashtags(text: str) -> str:
        """Remove hashtags from text while preserving the hashtag content"""
        return TextProcessor.HASHTAG_PATTERN.sub('', text)
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace - convert multiple spaces to single space"""
        text = TextProcessor.WHITESPACE_PATTERN.sub(' ', text)
        return text.strip()
    
    @staticmethod
    def remove_special_characters(text: str, keep_punctuation: bool = True) -> str:
        """
        Remove special characters but keep letters, numbers, and optional punctuation.
        Preserves Urdu characters.
        """
        if keep_punctuation:
            # Keep Urdu characters, English letters, numbers, punctuation, and whitespace
            text = re.sub(r'[^\w\s\u0600-\u06FF\-\.!?,\'"()]', '', text)
        else:
            text = TextProcessor.SPECIAL_CHAR_PATTERN.sub('', text)
        return text
    
    @staticmethod
    def lowercase(text: str) -> str:
        """Convert text to lowercase (appropriate for English, less for Urdu)"""
        return text.lower()
    
    @staticmethod
    def clean_text(
        text: str,
        remove_urls: bool = True,
        remove_mentions: bool = True,
        remove_hashtags: bool = False,
        lowercase: bool = True,
        normalize_whitespace: bool = True,
        remove_special_chars: bool = False,
    ) -> str:
        """
        Comprehensive text cleaning pipeline.
        
        Args:
            text: Raw input text
            remove_urls: Remove URLs
            remove_mentions: Remove @mentions
            remove_hashtags: Remove #hashtags
            lowercase: Convert to lowercase
            normalize_whitespace: Normalize spaces
            remove_special_chars: Remove special characters
            
        Returns:
            Cleaned text
        """
        original_length = len(text)
        
        # Remove URLs
        if remove_urls:
            text = TextProcessor.remove_urls(text)
        
        # Remove mentions
        if remove_mentions:
            text = TextProcessor.remove_mentions(text)
        
        # Remove hashtags
        if remove_hashtags:
            text = TextProcessor.remove_hashtags(text)
        
        # Remove special characters
        if remove_special_chars:
            text = TextProcessor.remove_special_characters(text, keep_punctuation=True)
        
        # Normalize whitespace first (remove extra spaces)
        if normalize_whitespace:
            text = TextProcessor.normalize_whitespace(text)
        
        # Convert to lowercase (mainly for English matching)
        if lowercase:
            text = TextProcessor.lowercase(text)
        
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
        """
        Truncate text to maximum length.
        Tries to cut at sentence boundaries when possible.
        """
        if len(text) <= max_length:
            return text
        
        # Try to cut at last period
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        if last_period > max_length * 0.8:  # Only if period is reasonably close
            return text[:last_period + 1]
        
        # Otherwise just truncate
        return truncated.rsplit(' ', 1)[0] if ' ' in truncated else truncated
    
    @staticmethod
    def validate_text(text: str) -> Tuple[bool, str]:
        """
        Validate text for analysis.
        
        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        if not text or not isinstance(text, str):
            return False, "Text is empty or not a string"
        
        text = text.strip()
        
        if len(text) < MIN_TEXT_LENGTH:
            return False, f"Text too short (minimum {MIN_TEXT_LENGTH} characters)"
        
        # Check if text contains mostly non-ASCII non-Unicode characters
        ascii_count = sum(1 for c in text if ord(c) < 128)
        if ascii_count < len(text) * 0.1 and not any('\u0600' <= c <= '\u06FF' for c in text):
            return False, "Text appears to be gibberish or invalid encoding"
        
        return True, ""
    
    @staticmethod
    def preprocess_for_inference(text: str) -> str:
        """
        Preprocess text specifically for model inference.
        Returns cleaned and validated text ready for ML models.
        """
        # Validate
        is_valid, reason = TextProcessor.validate_text(text)
        if not is_valid:
            return ""
        
        # Clean
        cleaned = TextProcessor.clean_text(
            text,
            remove_urls=True,
            remove_mentions=True,
            remove_hashtags=False,  # Keep hashtags as they can indicate sentiment
            lowercase=True,
            normalize_whitespace=True,
            remove_special_chars=False,
        )
        
        # Truncate if needed
        cleaned = TextProcessor.truncate_text(cleaned)
        
        return cleaned
