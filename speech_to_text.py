"""
Speech-to-Text Module for SignBridge Member 3 (Doctor -> Patient / Reverse ISL).

Handles audio acquisition from the doctor's microphone, ambient noise calibration,
speech recognition using SpeechRecognition (Google Web Speech API backend),
and deterministic medical text normalization.
"""

import re
import sys
from pathlib import Path
import speech_recognition as sr

# Add member3 root to path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))


def normalize_text(text: str) -> str:
    """
    Normalizes recognized speech text:
      - Converts to lowercase
      - Removes all punctuation (periods, commas, question marks, exclamation marks, quotes, etc.)
      - Replaces consecutive whitespace with a single space
      - Strips leading and trailing whitespace
    
    Examples:
      "Are you sick?" -> "are you sick"
      "Do you have medicine?" -> "do you have medicine"
      "Go to hospital, tomorrow!" -> "go to hospital tomorrow"
    """
    if not text:
        return ""
    
    # Convert to lowercase
    normalized = text.lower()
    
    # Remove punctuation, keeping alphanumeric characters and spaces
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    
    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized).strip()
    
    return normalized


def listen_to_doctor(timeout: float = 5.0, phrase_time_limit: float = 10.0) -> dict:
    """
    Opens the microphone, adjusts for ambient background noise, listens for doctor's speech,
    and converts speech to English text.

    Args:
        timeout (float): Maximum seconds to wait for speech to begin.
        phrase_time_limit (float): Maximum duration in seconds for the phrase.

    Returns:
        dict: {
            "success": bool,
            "text": str,          # Normalized text
            "raw_text": str,      # Raw recognized text
            "error": str | None   # Descriptive error message if any
        }
    """
    recognizer = sr.Recognizer()
    
    # Reasonable energy thresholds for healthcare room acoustics
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    try:
        # Check microphone availability
        with sr.Microphone() as source:
            # Calibrate for ambient background noise
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            
            # Listen to doctor's input
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        # Recognize speech using Google Web Speech API (free, reliable default for English)
        raw_text = recognizer.recognize_google(audio, language="en-US")
        norm_text = normalize_text(raw_text)

        return {
            "success": True,
            "text": norm_text,
            "raw_text": raw_text,
            "error": None
        }

    except sr.WaitTimeoutError:
        return {
            "success": False,
            "text": "",
            "raw_text": "",
            "error": "Listening timed out. No speech detected within the timeout window."
        }
    except sr.UnknownValueError:
        return {
            "success": False,
            "text": "",
            "raw_text": "",
            "error": "Speech was received but could not be understood. Please speak clearly into the microphone."
        }
    except sr.RequestError as e:
        return {
            "success": False,
            "text": "",
            "raw_text": "",
            "error": f"Speech recognition service error: {e}"
        }
    except OSError as e:
        return {
            "success": False,
            "text": "",
            "raw_text": "",
            "error": f"Microphone hardware error: {e}. Please ensure a working microphone is connected."
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "raw_text": "",
            "error": f"Unexpected error during speech recognition: {e}"
        }


def recognize_from_audio_file(audio_path: str | Path) -> dict:
    """
    Recognizes speech from an audio file (.wav, .flac, .aiff) for automated testing.
    """
    recognizer = sr.Recognizer()
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return {"success": False, "text": "", "raw_text": "", "error": f"Audio file not found: {audio_path}"}

    try:
        with sr.AudioFile(str(audio_path)) as source:
            audio = recognizer.record(source)
        raw_text = recognizer.recognize_google(audio, language="en-US")
        return {
            "success": True,
            "text": normalize_text(raw_text),
            "raw_text": raw_text,
            "error": None
        }
    except Exception as e:
        return {"success": False, "text": "", "raw_text": "", "error": str(e)}


if __name__ == "__main__":
    print("Testing normalization:")
    test_phrases = [
        "Are you sick?",
        "Do you have medicine?",
        "Go to hospital, tomorrow!",
        "  Doctor... Patient?!  "
    ]
    for tp in test_phrases:
        print(f"  {tp!r:30} -> {normalize_text(tp)!r}")
        
    print("\nMicrophone test (speak now, 3s timeout)...")
    res = listen_to_doctor(timeout=3, phrase_time_limit=4)
    print("Result:", res)
