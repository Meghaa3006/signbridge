"""
Configuration file for SignBridge Member 3 (Doctor -> Patient / Reverse ISL).
Contains controlled vocabulary, dataset labels, archive mappings, and filesystem paths.
"""

from pathlib import Path

# Base Paths
MEMBER3_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MEMBER3_DIR.parent
VIDEOS_DIR = MEMBER3_DIR / "videos"
DATA_DIR = MEMBER3_DIR / "data"

# Ensure crucial directories exist
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Zenodo INCLUDE Dataset Information
ZENODO_RECORD_ID = "4010759"
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"
ZENODO_BASE_FILES_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}/files"

# Controlled Vocabulary for Member 3
# Exact Zenodo INCLUDE original labels preserved alongside normalized keys and folder names.
CONTROLLED_VOCABULARY = {
    "doctor": {
        "dataset_label": "87. Doctor",
        "folder_name": "Doctor",
        "display_name": "Doctor",
        "archive": "Jobs_1of2.zip",
        "archive_path_prefix": "Jobs/87. Doctor"
    },
    "patient": {
        "dataset_label": "88. Patient",
        "folder_name": "Patient",
        "display_name": "Patient",
        "archive": "Jobs_1of2.zip",
        "archive_path_prefix": "Jobs/88. Patient"
    },
    "hospital": {
        "dataset_label": "30. Hospital",
        "folder_name": "Hospital",
        "display_name": "Hospital",
        "archive": "Places_3of4.zip",
        "archive_path_prefix": "Places/30. Hospital"
    },
    "medicine": {
        "dataset_label": "3. Medicine",
        "folder_name": "Medicine",
        "display_name": "Medicine",
        "archive": "Society_1of3.zip",
        "archive_path_prefix": "Society/3. Medicine"
    },
    "sick": {
        "dataset_label": "98. sick",
        "folder_name": "sick",
        "display_name": "Sick",
        "archive": "Adjectives_8of8.zip",
        "archive_path_prefix": "Adjectives/98. sick"
    },
    "healthy": {
        "dataset_label": "99. healthy",
        "folder_name": "healthy",
        "display_name": "Healthy",
        "archive": "Adjectives_8of8.zip",
        "archive_path_prefix": "Adjectives/99. healthy"
    },
    "today": {
        "dataset_label": "73. Today",
        "folder_name": "Today",
        "display_name": "Today",
        "archive": "Days_and_Time_1of3.zip",
        "archive_path_prefix": "Days_and_Time/73. Today"
    },
    "tomorrow": {
        "dataset_label": "74. Tomorrow",
        "folder_name": "Tomorrow",
        "display_name": "Tomorrow",
        "archive": "Days_and_Time_2of3.zip",
        "archive_path_prefix": "Days_and_Time/74. Tomorrow"
    }
}

# Simplified key-to-label map as requested in Section 5
VOCABULARY_MAP = {k: v["dataset_label"] for k, v in CONTROLLED_VOCABULARY.items()}

# List of required video folders
REQUIRED_FOLDERS = [v["folder_name"] for v in CONTROLLED_VOCABULARY.values()]

# Supported video extensions
SUPPORTED_VIDEO_EXTENSIONS = [".mov", ".MOV", ".mp4", ".MP4", ".webm", ".WEBM"]

# Safety Disclaimer
MEDICAL_SAFETY_DISCLAIMER = (
    "NOTICE: SignBridge is an assistive communication bridge designed to facilitate basic dialogue "
    "between healthcare providers and deaf/hard-of-hearing patients. It is NOT a medical diagnosis, "
    "treatment, or clinical inference system. Never substitute this tool for certified professional "
    "medical interpreters in clinical settings."
)
