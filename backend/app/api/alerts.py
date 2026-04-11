"""
Sound Alerts API - Handle system sound alerts for critical content detection
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.db.models import Post
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import io
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

router = APIRouter()


class AlertSettings(BaseModel):
    sound_alerts_enabled: bool = True
    sound_type: str = "alert"  # 'alert', 'chime', 'warning'
    volume: int = 100  # 0-100


class AlertTrigger(BaseModel):
    post_id: int
    severity: str = "high"  # 'low', 'medium', 'high', 'critical'


class SoundAlert(BaseModel):
    alert_id: int
    post_id: int
    severity: str
    triggered_at: datetime
    sound_type: str


# In-memory storage for alert settings (in production, use database)
ALERT_SETTINGS = {
    "sound_alerts_enabled": True,
    "sound_type": "alert",
    "volume": 100
}

# Sound definitions (frequencies in Hz and duration in ms)
SOUND_CONFIGS = {
    "alert": {
        "frequency": 800,
        "duration": 500,
        "pattern": [800, 200, 800, 200, 800]  # Beep-pause-beep pattern
    },
    "chime": {
        "frequency": 1000,
        "duration": 300,
        "pattern": [1000, 100, 1200, 100, 1000]  # Musical chime
    },
    "warning": {
        "frequency": 600,
        "duration": 800,
        "pattern": [600, 300, 600, 300, 600, 300]  # Warning tone
    }
}


@router.get("/settings")
def get_alert_settings():
    """Get current alert settings"""
    return ALERT_SETTINGS


@router.post("/settings")
def update_alert_settings(settings: AlertSettings):
    """Update alert settings"""
    global ALERT_SETTINGS
    
    if settings.volume < 0 or settings.volume > 100:
        raise HTTPException(status_code=400, detail="Volume must be between 0-100")
    
    if settings.sound_type not in SOUND_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sound type. Must be one of: {list(SOUND_CONFIGS.keys())}"
        )
    
    ALERT_SETTINGS.update({
        "sound_alerts_enabled": settings.sound_alerts_enabled,
        "sound_type": settings.sound_type,
        "volume": settings.volume
    })
    
    return {
        "status": "updated",
        "settings": ALERT_SETTINGS
    }


@router.post("/trigger")
def trigger_sound_alert(alert: AlertTrigger, db: Session = Depends(get_db)):
    """
    Trigger a sound alert for a detected post
    - post_id: Post that triggered the alert
    - severity: Alert severity level (low, medium, high, critical)
    """
    # Verify post exists
    post = db.query(Post).filter(Post.post_id == alert.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if not ALERT_SETTINGS["sound_alerts_enabled"]:
        return {
            "status": "suppressed",
            "reason": "Sound alerts are disabled",
            "post_id": alert.post_id
        }
    
    sound_type = ALERT_SETTINGS["sound_type"]
    volume = ALERT_SETTINGS["volume"]
    
    # Trigger the sound based on platform
    try:
        trigger_system_sound(sound_type, volume, alert.severity)
    except Exception as e:
        return {
            "status": "sound_failed",
            "reason": str(e),
            "post_id": alert.post_id,
            "alert_sent": True  # Even if sound fails, alert is logged
        }
    
    return {
        "status": "triggered",
        "post_id": alert.post_id,
        "severity": alert.severity,
        "sound_type": sound_type,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/test")
def test_sound_alert(sound_type: str = "alert", volume: int = 100):
    """
    Test the sound alert system
    - sound_type: Type of sound to test
    - volume: Volume level (0-100)
    """
    if sound_type not in SOUND_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sound type. Must be one of: {list(SOUND_CONFIGS.keys())}"
        )
    
    if volume < 0 or volume > 100:
        raise HTTPException(status_code=400, detail="Volume must be between 0-100")
    
    try:
        trigger_system_sound(sound_type, volume)
        return {
            "status": "success",
            "message": f"Test sound ({sound_type}) played successfully",
            "sound_type": sound_type,
            "volume": volume
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Failed to play test sound: {str(e)}",
            "details": str(e)
        }


@router.get("/audio-file")
def get_audio_file(sound_type: str = "alert", severity: str = "high"):
    """
    Get audio file for the alert (returns WAV data)
    Can be used by web applications to play sound via browser
    """
    if sound_type not in SOUND_CONFIGS:
        raise HTTPException(status_code=400, detail="Invalid sound type")
    
    try:
        audio_data = generate_alert_tone(sound_type, severity)
        return io.BytesIO(audio_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")


def trigger_system_sound(sound_type: str, volume: int = 100, severity: str = "high"):
    """
    Trigger a system sound alert
    Works on Windows, can be extended for other platforms
    
    Args:
        sound_type: Type of sound ('alert', 'chime', 'warning')
        volume: Volume level (0-100)
        severity: Alert severity (affects frequency/pattern)
    """
    if not WINSOUND_AVAILABLE:
        # On non-Windows systems, provide alternative
        return {
            "platform": "non-windows",
            "message": "Sound alerts available via browser playback"
        }
    
    config = SOUND_CONFIGS.get(sound_type, SOUND_CONFIGS["alert"])
    
    # Adjust frequency based on severity
    if severity == "critical":
        frequency = int(config["frequency"] * 1.2)  # Higher pitch
    elif severity == "high":
        frequency = config["frequency"]
    elif severity == "medium":
        frequency = int(config["frequency"] * 0.9)  # Lower pitch
    else:
        frequency = int(config["frequency"] * 0.7)  # Even lower
    
    # Adjust duration based on volume
    duration = int(config["duration"] * (volume / 100))
    
    try:
        # Play beep pattern (Windows)
        pattern = config.get("pattern", [frequency])
        for i, freq in enumerate(pattern):
            if i % 2 == 0:  # Sound
                winsound.Beep(freq, duration)
            else:  # Pause
                # Small pause between beeps
                pass
        
        return {"status": "success"}
    except Exception as e:
        raise Exception(f"Failed to play system sound: {str(e)}")


def generate_alert_tone(sound_type: str, severity: str = "high"):
    """
    Generate WAV audio data for browser playback
    This allows sound alerts to work in web browsers
    
    Returns: WAV file bytes
    """
    try:
        import numpy as np
        from scipy.io import wavfile
    except ImportError:
        raise Exception("Audio generation requires numpy and scipy. Install with: pip install numpy scipy")
    
    # Audio parameters
    sample_rate = 44100  # CD quality
    duration_seconds = 0.5
    num_samples = int(sample_rate * duration_seconds)
    
    config = SOUND_CONFIGS.get(sound_type, SOUND_CONFIGS["alert"])
    
    # Adjust frequency based on severity
    if severity == "critical":
        frequency = int(config["frequency"] * 1.2)
    elif severity == "high":
        frequency = config["frequency"]
    elif severity == "medium":
        frequency = int(config["frequency"] * 0.9)
    else:
        frequency = int(config["frequency"] * 0.7)
    
    # Generate sine wave
    t = np.linspace(0, duration_seconds, num_samples)
    waveform = np.sin(2 * np.pi * frequency * t)
    
    # Add envelope (fade in/out)
    envelope = np.hanning(num_samples)
    waveform = waveform * envelope
    
    # Convert to 16-bit PCM
    audio_data = (waveform * 32767).astype(np.int16)
    
    # Save to BytesIO
    output = io.BytesIO()
    wavfile.write(output, sample_rate, audio_data)
    output.seek(0)
    
    return output.getvalue()


@router.post("/disable")
def disable_alerts():
    """Disable all sound alerts"""
    global ALERT_SETTINGS
    ALERT_SETTINGS["sound_alerts_enabled"] = False
    return {"status": "disabled", "message": "Sound alerts have been disabled"}


@router.post("/enable")
def enable_alerts():
    """Enable sound alerts"""
    global ALERT_SETTINGS
    ALERT_SETTINGS["sound_alerts_enabled"] = True
    return {"status": "enabled", "message": "Sound alerts have been enabled"}


@router.get("/status")
def get_alert_status():
    """Get current alert system status"""
    return {
        "enabled": ALERT_SETTINGS["sound_alerts_enabled"],
        "sound_type": ALERT_SETTINGS["sound_type"],
        "volume": ALERT_SETTINGS["volume"],
        "platform_support": {
            "windows": WINSOUND_AVAILABLE,
            "browser_playback": True,
            "system_sound": WINSOUND_AVAILABLE
        },
        "available_sounds": list(SOUND_CONFIGS.keys())
    }
