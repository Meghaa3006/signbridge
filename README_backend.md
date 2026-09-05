# SignBridge — Member 3 Module
## Doctor → Patient | Reverse Indian Sign Language (ISL)

This module is the **Reverse ISL pipeline** of the SignBridge assistive communication system for healthcare consultations. It captures the doctor's spoken dialogue, normalizes the text, matches against approved healthcare Indian Sign Language vocabulary from the **AI4Bharat INCLUDE dataset (IIT Madras)**, and displays authentic ISL videos to deaf / hard-of-hearing patients.

---

## 1. System Pipeline

```
Doctor Spoken Audio
       ↓
Microphone Input
       ↓
Speech-to-Text (SpeechRecognition / Google Web Speech API)
       ↓
Recognized English Text
       ↓
Deterministic Medical Text Normalization
       ↓
Controlled Phrase Matching (Controlled Vocabulary)
       ↓
Authentic INCLUDE Dataset Sign Selection
       ↓
Patient Screen (Streamlit Video Player with Fullscreen/Replay)
```

---

## 2. Controlled Vocabulary & Dataset Mapping

Based strictly on the **INCLUDE dataset (Zenodo Record 4010759)**:

| Sign Key | Display Name | Original Dataset Label | Source Archive | Target Directory |
| :--- | :--- | :--- | :--- | :--- |
| `doctor` | Doctor | `87. Doctor` | `Jobs_1of2.zip` | `videos/Doctor/` |
| `patient` | Patient | `88. Patient` | `Jobs_1of2.zip` | `videos/Patient/` |
| `hospital` | Hospital | `30. Hospital` | `Places_3of4.zip` | `videos/Hospital/` |
| `medicine` | Medicine | `3. Medicine` | `Society_1of3.zip` | `videos/Medicine/` |
| `sick` | Sick | `98. sick` | `Adjectives_8of8.zip` | `videos/sick/` |
| `healthy` | Healthy | `99. healthy` | `Adjectives_8of8.zip` | `videos/healthy/` |
| `today` | Today | `73. Today` | `Days_and_Time_1of3.zip` | `videos/Today/` |
| `tomorrow` | Tomorrow | `74. Tomorrow` | `Days_and_Time_2of3.zip` | `videos/Tomorrow/` |

> **Crucial Rule**: The system displays *only* actual videos that exist in the downloaded INCLUDE dataset. No synthetic or hallucinated filenames (such as `go_to_hospital.mp4`) are ever generated.

---

## 3. Installation & Setup

### 3.1 Install Dependencies
```bash
pip install -r member3/requirements.txt
```

Core dependencies:
- `streamlit>=1.30.0`: Clinical interface with video player
- `SpeechRecognition>=3.10.0`: Doctor speech recognition
- `PyAudio>=0.2.14`: Microphone audio input binding

---

## 4. Dataset Download & Selective Extraction

The complete INCLUDE dataset is 56+ GB across 43 archives. **Do NOT download the entire dataset.**

Our selective downloader connects to Zenodo via HTTP Range requests and streams *only* the specific authentic `.MOV` video files directly into `member3/videos/<category>/`:

### Download Sample Dataset (Recommended for Hackathon - Fast Setup)
Downloads 1–2 authentic videos per category in under 2 minutes:
```bash
python member3/dataset/download_required_data.py --sample 2
```

### Download Full Vocabulary Set
Downloads all 132 videos across the 8 categories (~1.4 GB total):
```bash
python member3/dataset/download_required_data.py --all
```

---

## 5. Dataset Validation

Verify that all required folders exist, videos are present, and video formats are valid:

```bash
python member3/dataset/validate_dataset.py
```

Expected output:
```
=============================================
INCLUDE Dataset Validation
=============================================
Doctor       ✓ 1 videos
Patient      ✓ 1 videos
Hospital     ✓ 1 videos
Medicine     ✓ 1 videos
sick         ✓ 1 videos
healthy      ✓ 1 videos
Today        ✓ 1 videos
Tomorrow     ✓ 1 videos
---------------------------------------------
Dataset validation completed: ALL REQUIRED CLASSES PRESENT ✓
Total active classes: 8
Total videos available: 8
=============================================
```

---

## 6. Running the Streamlit Application

Launch the clinical user interface:

```bash
streamlit run member3/app.py
```

Open your browser at `http://localhost:8501`.

### Key Features:
- **Live Microphone Input**: Click `[ 🎤 Start Listening ]`. Status updates dynamically: `READY` → `LISTENING...` → `PROCESSING...` → Displays ISL Video.
- **Manual Text Simulation**: Type any doctor statement (e.g. `Are you sick?` or `Go to hospital tomorrow.`) and click `[ Process Text ]`.
- **🎯 Demo Mode**: Fallback dropdown with all 8 signs and preset healthcare phrases. Perfect for live hackathon presentations when a microphone is unavailable.
- **Multi-Sign Sequencing**: Sentences with multiple signs (e.g., `Go to hospital tomorrow.`) automatically create sequential video tabs for each detected sign.
- **Dataset Status Monitor**: Real-time indicator in the sidebar showing available classes and video counts.

---

## 7. Member 4 Integration Interface

Member 4 can import and call `process_doctor_speech(text)` directly without any Streamlit dependencies:

```python
from member3.phrase_mapper import process_doctor_speech

# Example 1: Single Sign
result = process_doctor_speech("Are you sick?")
print(result)
# Output:
# {
#   "recognized_text": "are you sick",
#   "matched_signs": [
#     {
#       "sign": "sick",
#       "dataset_label": "98. sick",
#       "video_path": "videos/sick/MVI_5170.MOV"
#     }
#   ],
#   "success": True
# }

# Example 2: Multi-Sign Sentence
result = process_doctor_speech("Go to hospital tomorrow.")
print(result)
# Output:
# {
#   "recognized_text": "go to hospital tomorrow",
#   "matched_signs": [
#     {
#       "sign": "hospital",
#       "dataset_label": "30. Hospital",
#       "video_path": "videos/Hospital/MVI_3315.MOV"
#     },
#     {
#       "sign": "tomorrow",
#       "dataset_label": "74. Tomorrow",
#       "video_path": "videos/Tomorrow/MVI_4619.MOV"
#     }
#   ],
#   "success": True
# }
```

---

## 8. Automated Testing

Run the automated test suite covering all 8 signs, multi-sign sequencing, phrase rejection, and normalization:

```bash
python -m unittest member3/tests/test_phrase_mapper.py
```

---

## 9. Medical Safety Notice

> **IMPORTANT**: SignBridge is strictly an assistive communication aid designed to facilitate basic conversation between healthcare professionals and deaf/hard-of-hearing patients. It does **not** diagnose medical conditions, recommend treatments, or make clinical evaluations. Only approved, verified ISL signs from the INCLUDE dataset are displayed.
