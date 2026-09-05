"""
Phrase Mapper Module for SignBridge Member 3 (Doctor -> Patient / Reverse ISL).

Performs controlled phrase matching from doctor speech against the 8 approved
INCLUDE dataset categories, locates authentic verified video files, supports
multi-sign detection in sentence order, and provides the Member 4 integration API.
"""

import sys
import os
from pathlib import Path

# Add member3 root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import (
    CONTROLLED_VOCABULARY,
    VIDEOS_DIR,
    SUPPORTED_VIDEO_EXTENSIONS,
    MEMBER3_DIR
)
from speech_to_text import normalize_text


def find_sign_video(sign_key: str, video_index: int = 0) -> str | None:
    """
    Locates the correct dataset category directory, discovers available authentic videos,
    and returns a valid video path.

    Rules:
      - Never hallucinate or invent fake video filenames (e.g. 'go_to_hospital.mp4').
      - Returns None if the category or video does not exist on disk.
      - Returns a relative or absolute path to an actual existing file.

    Args:
        sign_key (str): Normalized sign key (e.g. 'doctor', 'sick', 'hospital')
        video_index (int): Optional index if multiple video recordings exist for this sign.

    Returns:
        str | None: String path to the verified video file, or None if unavailable.
    """
    sign_key = sign_key.lower().strip()
    if sign_key not in CONTROLLED_VOCABULARY:
        return None

    folder_name = CONTROLLED_VOCABULARY[sign_key]["folder_name"]
    category_dir = VIDEOS_DIR / folder_name

    if not category_dir.exists() or not category_dir.is_dir():
        return None

    # Find all supported video files
    video_files = sorted([
        f for f in category_dir.iterdir()
        if f.is_file() and f.suffix in SUPPORTED_VIDEO_EXTENSIONS and f.stat().st_size > 0
    ])

    if not video_files:
        return None

    selected = video_files[video_index % len(video_files)]
    # Return path relative to Member 3 or absolute
    try:
        rel_path = selected.relative_to(MEMBER3_DIR)
        return str(rel_path).replace("\\", "/")
    except ValueError:
        return str(selected).replace("\\", "/")


def match_sign(normalized_text: str) -> dict:
    """
    Identifies the primary approved dataset sign present in the doctor's speech.
    Matches Requirement 9 contract:
      {
        "matched": True,
        "sign": "sick",
        "dataset_label": "98. sick",
        "video_path": "videos/sick/..."
      }
      or
      {
        "matched": False,
        "sign": None,
        "video_path": None
      }
    """
    signs = match_signs(normalized_text)
    if signs:
        first = signs[0]
        return {
            "matched": True,
            "sign": first["sign"],
            "dataset_label": first["dataset_label"],
            "video_path": first["video_path"]
        }
    return {
        "matched": False,
        "sign": None,
        "video_path": None
    }


def match_signs(normalized_text: str) -> list[dict]:
    """
    Identifies all approved vocabulary signs present in the doctor's speech,
    ordered by their occurrence in the spoken sentence.

    Supports single words and multi-sign phrases (e.g., 'Go to hospital tomorrow'
    -> ['hospital', 'tomorrow']).
    """
    if not normalized_text:
        return []

    tokens = normalize_text(normalized_text).split()
    if not tokens:
        return []

    # Map token position to detected vocabulary sign
    detected_positions = []
    
    for i, token in enumerate(tokens):
        # Direct word match against vocabulary keys
        if token in CONTROLLED_VOCABULARY:
            detected_positions.append((i, token))

    # Sort in order of appearance in the sentence
    detected_positions.sort(key=lambda x: x[0])

    matched_signs = []
    seen = set()
    for _, sign_key in detected_positions:
        if sign_key in seen:
            continue
        seen.add(sign_key)
        
        info = CONTROLLED_VOCABULARY[sign_key]
        video_path = find_sign_video(sign_key)
        
        matched_signs.append({
            "sign": sign_key,
            "display_name": info["display_name"],
            "dataset_label": info["dataset_label"],
            "folder_name": info["folder_name"],
            "video_path": video_path
        })

    return matched_signs


def process_doctor_speech(text: str) -> dict:
    """
    Public Integration Interface for Member 4.
    Does NOT depend on Streamlit.

    Input:
        text (str): Doctor's recognized speech (e.g. 'Are you sick?' or 'Go to hospital tomorrow.')

    Output:
        dict: {
            "recognized_text": "are you sick",
            "matched_signs": [
                {
                    "sign": "sick",
                    "dataset_label": "98. sick",
                    "video_path": "videos/sick/MVI_5170.MOV"
                }
            ],
            "success": True
        }
    """
    norm = normalize_text(text)
    signs = match_signs(norm)
    
    # Strip internal display_name/folder_name to conform precisely to Member 4 contract
    cleaned_signs = [
        {
            "sign": s["sign"],
            "dataset_label": s["dataset_label"],
            "video_path": s["video_path"]
        }
        for s in signs
    ]
    
    return {
        "recognized_text": norm,
        "matched_signs": cleaned_signs,
        "success": len(cleaned_signs) > 0
    }


if __name__ == "__main__":
    sample_tests = [
        "Doctor",
        "Patient",
        "Hospital",
        "Medicine",
        "Are you sick?",
        "Are you healthy?",
        "Today",
        "Tomorrow",
        "Go to hospital tomorrow.",
        "What is the weather outside?"
    ]
    print("Testing process_doctor_speech():")
    for t in sample_tests:
        res = process_doctor_speech(t)
        print(f"\nDoctor said: {t!r}")
        print(f"Result: {res}")
