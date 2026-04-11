"""
AI Pipeline for Vigilis - Real-time text analysis for detecting hate speech, extremism, and misinformation.

Supports English, Urdu, and mixed language text using state-of-the-art transformer models.

## Quick Start

```python
from ai_pipeline.integration import AIAnalysisPipeline

# Initialize pipeline (loads models on first use)
pipeline = AIAnalysisPipeline()

# Analyze a single post
result = pipeline.analyzer.analyze_text(
    "This is some harmful text"
)

print(f"Hate Score: {result.hate_score}")
print(f"Flagged: {result.flagged}")
print(f"Reasons: {result.flags_triggered}")

# Or analyze and save in one step (requires DB session)
post_id = pipeline.analyze_and_save(
    db=db_session,
    source_id=1,
    author="@username",
    text_content="Post content",
    timestamp=datetime.utcnow(),
    category="twitter"
)
```

## Modules

- **config.py** - Configuration and thresholds
- **text_processor.py** - Text cleaning and preprocessing
- **models_loader.py** - Transformer model management
- **analyzer.py** - Core analysis engine
- **db_operations.py** - Database operations
- **integration.py** - Pipeline orchestration
- **api_endpoints.py** - FastAPI REST endpoints
- **scraper_integration_example.py** - Integration patterns

## Key Features

- ✅ Real-time analysis as posts are scraped
- ✅ Async/concurrent processing support
- ✅ Only stores flagged posts (database efficient)
- ✅ Multilingual support (English, Urdu, mixed)
- ✅ 8 different risk scores per post
- ✅ Configurable severity thresholds
- ✅ Queue-based processing for high volume
- ✅ FastAPI endpoints for dashboard
"""

from .analyzer import TextAnalyzer, AnalysisResult
from .models_loader import ModelsLoader
from .integration import AIAnalysisPipeline, PostAnalysisQueue
from .text_processor import TextProcessor
from .db_operations import AnalyzedPostDB
from . import config

__all__ = [
    "TextAnalyzer",
    "AnalysisResult",
    "ModelsLoader",
    "AIAnalysisPipeline",
    "PostAnalysisQueue",
    "TextProcessor",
    "AnalyzedPostDB",
    "config",
]

