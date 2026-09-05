"""
Dataset Validation Script for SignBridge Member 3.
Checks that all required INCLUDE sign categories exist in member3/videos/,
contain valid video files with supported extensions, and reports video counts.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path so config can be imported
CURRENT_DIR = Path(__file__).resolve().parent
MEMBER3_DIR = CURRENT_DIR.parent
if str(MEMBER3_DIR) not in sys.path:
    sys.path.insert(0, str(MEMBER3_DIR))

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import CONTROLLED_VOCABULARY, VIDEOS_DIR, SUPPORTED_VIDEO_EXTENSIONS


def get_dataset_status() -> dict:
    """
    Inspects the member3/videos directory and returns detailed status for each sign.
    Returns:
        dict: Mapping from sign_key to {
            "folder_name": str,
            "dataset_label": str,
            "display_name": str,
            "exists": bool,
            "count": int,
            "videos": list[str],
            "status": str ("valid", "empty", "missing")
        }
    """
    status = {}
    for key, info in CONTROLLED_VOCABULARY.items():
        folder_name = info["folder_name"]
        folder_path = VIDEOS_DIR / folder_name
        
        if not folder_path.exists() or not folder_path.is_dir():
            status[key] = {
                "folder_name": folder_name,
                "dataset_label": info["dataset_label"],
                "display_name": info["display_name"],
                "exists": False,
                "count": 0,
                "videos": [],
                "status": "missing"
            }
            continue
            
        # Scan for supported video files
        video_files = [
            f.name for f in folder_path.iterdir()
            if f.is_file() and f.suffix in SUPPORTED_VIDEO_EXTENSIONS and f.stat().st_size > 0
        ]
        
        status[key] = {
            "folder_name": folder_name,
            "dataset_label": info["dataset_label"],
            "display_name": info["display_name"],
            "exists": True,
            "count": len(video_files),
            "videos": sorted(video_files),
            "status": "valid" if len(video_files) > 0 else "empty"
        }
        
    return status


def validate_dataset() -> bool:
    """
    Validates the dataset and prints a formatted report to console.
    Returns True if all required classes have at least 1 video, False otherwise.
    """
    print("=" * 45)
    print("INCLUDE Dataset Validation")
    print("=" * 45)
    
    status = get_dataset_status()
    all_valid = True
    missing_classes = []
    
    for key, info in CONTROLLED_VOCABULARY.items():
        stat = status[key]
        display = stat["folder_name"]
        count = stat["count"]
        
        if stat["status"] == "valid":
            print(f"{display:<12} \u2713 {count} videos")
        elif stat["status"] == "empty":
            print(f"{display:<12} \u26a0 folder exists but 0 videos found")
            all_valid = False
            missing_classes.append(display)
        else:
            print(f"{display:<12} \u26a0 Video data not found")
            all_valid = False
            missing_classes.append(display)
            
    print("-" * 45)
    if all_valid:
        print("Dataset validation completed: ALL REQUIRED CLASSES PRESENT \u2713")
        print(f"Total active classes: {len(status)}")
        total_videos = sum(s["count"] for s in status.values())
        print(f"Total videos available: {total_videos}")
    else:
        print("Dataset validation completed: MISSING OR EMPTY CLASSES \u26a0")
        print(f"Missing/empty: {', '.join(missing_classes)}")
        print("Run: python member3/dataset/download_required_data.py to download required videos.")
    print("=" * 45)
    
    return all_valid


if __name__ == "__main__":
    success = validate_dataset()
    sys.exit(0 if success else 1)
