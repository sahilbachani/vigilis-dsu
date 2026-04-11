"""
Model Loader Module
Manages loading, caching, and inference with transformer models.
Supports lazy loading or eager loading at startup.
"""

import logging
from typing import Dict, Optional, Tuple
import torch
from .config import (
    MODELS_CONFIG,
    CACHE_MODELS,
    USE_GPU,
    DEVICE,
    LOAD_ON_STARTUP,
)

# Lazy import - transformers will be imported only when needed
pipeline = None
Pipeline = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _ensure_transformers_imported():
    """Lazily import transformers only when needed"""
    global pipeline, Pipeline
    if pipeline is None:
        try:
            from transformers import pipeline as tf_pipeline, Pipeline as TfPipeline
            pipeline = tf_pipeline
            Pipeline = TfPipeline
        except ImportError as e:
            logger.error(f"Failed to import transformers: {e}")
            raise


class ModelsLoader:
    """
    Manages loading and caching of ML models.
    Loads models once at startup and reuses them for inference.
    """
    
    _instance = None  # Singleton pattern
    _models_cache: Dict[str, Pipeline] = {}
    _loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelsLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the models loader"""
        if not ModelsLoader._loaded:
            self.device = self._get_device()
            if LOAD_ON_STARTUP:
                self.load_all_models()
            ModelsLoader._loaded = True
    
    @staticmethod
    def _get_device() -> str:
        """Determine which device to use (GPU or CPU)"""
        if USE_GPU and torch.cuda.is_available():
            device = "cuda"
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            logger.info("Using CPU for inference")
        return device
    
    def load_model(self, model_key: str) -> Optional[Pipeline]:
        """
        Load a specific model by key.
        Returns cached version if already loaded.
        
        Args:
            model_key: Key from MODELS_CONFIG (e.g., 'hate_speech_detection')
            
        Returns:
            Loaded model pipeline or None if loading fails
        """
        # Ensure transformers is imported
        _ensure_transformers_imported()
        
        # Check cache first
        if CACHE_MODELS and model_key in self._models_cache:
            logger.info(f"Using cached model: {model_key}")
            return self._models_cache[model_key]
        
        # Get model config
        if model_key not in MODELS_CONFIG:
            logger.error(f"Unknown model: {model_key}")
            return None
        
        config = MODELS_CONFIG[model_key]
        model_name = config["model_name"]
        
        try:
            logger.info(f"Loading model: {model_name} for {model_key}...")
            
            # Load the pipeline
            pipe = pipeline(
                task=config["task"],
                model=model_name,
                device=0 if self.device == "cuda" else -1,  # -1 for CPU
                trust_remote_code=True
            )
            
            # Cache if enabled
            if CACHE_MODELS:
                self._models_cache[model_key] = pipe
            
            logger.info(f"✓ Model loaded successfully: {model_key}")
            return pipe
            
        except Exception as e:
            logger.error(f"✗ Failed to load model {model_key}: {str(e)}")
            return None
    
    def load_all_models(self) -> Dict[str, bool]:
        """
        Load all models defined in MODELS_CONFIG.
        
        Returns:
            Dictionary with model keys and their load status
        """
        logger.info("=" * 60)
        logger.info("Loading all AI models (this may take a few minutes)...")
        logger.info("=" * 60)
        
        load_status = {}
        for model_key in MODELS_CONFIG.keys():
            model = self.load_model(model_key)
            load_status[model_key] = model is not None
        
        logger.info("=" * 60)
        successful = sum(1 for v in load_status.values() if v)
        total = len(load_status)
        logger.info(f"Model loading complete: {successful}/{total} models loaded")
        logger.info("=" * 60)
        
        return load_status
    
    def get_model(self, model_key: str) -> Optional[Pipeline]:
        """
        Get a model, loading it if not already loaded.
        Safe to call multiple times.
        """
        if CACHE_MODELS and model_key in self._models_cache:
            return self._models_cache[model_key]
        
        return self.load_model(model_key)
    
    def unload_model(self, model_key: str) -> None:
        """Unload a specific model from cache"""
        if model_key in self._models_cache:
            del self._models_cache[model_key]
            logger.info(f"Unloaded model: {model_key}")
    
    def unload_all_models(self) -> None:
        """Unload all cached models"""
        self._models_cache.clear()
        logger.info("All models unloaded from cache")
    
    def get_loaded_models(self) -> Dict[str, bool]:
        """Get status of all models (loaded or not)"""
        status = {}
        for model_key in MODELS_CONFIG.keys():
            status[model_key] = model_key in self._models_cache
        return status
    
    @staticmethod
    def create_singleton() -> "ModelsLoader":
        """Factory method to create or get singleton instance"""
        return ModelsLoader()
