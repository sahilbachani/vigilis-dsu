"""
Configuration for AI Pipeline
Defines model names, thresholds, and processing parameters
"""

# Model Configuration
MODELS_CONFIG = {
    "hate_speech_detection": {
        "model_name": "Hate-speech-BERT-base",
        "source": "Hate-speech-BERT-base",
        "task": "text-classification",
        "description": "Detects hate speech and offensive language"
    },
    "extremism_detection": {
        "model_name": "xlm-roberta-base",
        "source": "xlm-roberta-base",
        "task": "text-classification",
        "description": "Detects extremist content using multilingual RoBERTa"
    },
    "misinformation_detection": {
        "model_name": "roberta-base-openai-detector",
        "source": "roberta-base-openai-detector",
        "task": "text-classification",
        "description": "Detects misinformation and machine-generated text"
    },
    "emotion_detection": {
        "model_name": "distilbert-base-uncased-finetuned-emotion",
        "source": "distilbert-base-uncased-finetuned-emotion",
        "task": "text-classification",
        "description": "Detects emotional intensity (anger, fear, disgust, neutral)"
    }
}

# Language Support
SUPPORTED_LANGUAGES = ["en", "ur", "mixed"]
DEFAULT_LANGUAGE = "en"

# Scoring Thresholds for Flagging
FLAGGING_THRESHOLDS = {
    "hate_score": 0.5,           # Flag if hate_score > 0.5
    "extremism_score": 0.5,      # Flag if extremism_score > 0.5
    "misinformation_score": 0.6, # Flag if misinformation_score > 0.6
    "emotion_anger": 0.7,        # Flag if anger emotion > 0.7
    "emotion_fear": 0.7,         # Flag if fear emotion > 0.7
    "emotion_disgust": 0.7,      # Flag if disgust emotion > 0.7
}

# Minimum confidence for considering a prediction valid
MIN_CONFIDENCE_THRESHOLD = 0.3

# Batch processing settings
BATCH_SIZE = 32
MAX_CONCURRENT_ANALYSES = 4
QUEUE_TIMEOUT = 30  # seconds

# Text processing limits
MAX_TEXT_LENGTH = 512  # Maximum tokens for models
MIN_TEXT_LENGTH = 10   # Minimum characters for analysis

# Cache settings
CACHE_MODELS = True  # Cache loaded models in memory
CACHE_EMBEDDINGS = False  # Don't cache embeddings (memory intensive)

# Logging
LOG_LEVEL = "INFO"
LOG_PREDICTIONS = True  # Log individual predictions for debugging

# Model loading strategy
LOAD_ON_STARTUP = True  # Load all models when application starts
LAZY_LOAD = False      # Load models on first use (if LOAD_ON_STARTUP is False)

# GPU/CPU Settings
USE_GPU = False  # Set to True if GPU is available
DEVICE = "cpu"   # or "cuda" if USE_GPU is True

# Emotion Detection Label Mapping
EMOTION_LABELS = {
    "anger": "emotion_anger",
    "fear": "emotion_fear",
    "disgust": "emotion_disgust",
    "neutral": "emotion_neutral",
    "joy": "emotion_joy",
    "sadness": "emotion_sadness",
}

# Hate Speech Detection Label Mapping
HATE_SPEECH_LABELS = {
    "hate_speech": 1,
    "offensive": 0.7,
    "neither": 0,
}

# Output file paths (optional)
PREDICTIONS_LOG_PATH = "logs/predictions.jsonl"
ERRORS_LOG_PATH = "logs/errors.log"
