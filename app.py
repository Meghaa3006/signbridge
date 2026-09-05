"""
SignBridge - Member 3: Doctor -> Patient / Reverse ISL
Streamlit Web Application

Pipeline:
  Doctor Spoken Speech / Input
  -> Speech-to-Text & Text Normalization
  -> Controlled Vocabulary Phrase Mapping
  -> Authentic INCLUDE Dataset Video Selection
  -> High-Definition Patient Screen & Video Playback
"""

import sys
import os
import time
from pathlib import Path
import streamlit as st

# Setup Path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import (
    CONTROLLED_VOCABULARY,
    VIDEOS_DIR,
    MEDICAL_SAFETY_DISCLAIMER,
    MEMBER3_DIR
)
from speech_to_text import normalize_text, listen_to_doctor
from phrase_mapper import match_signs, process_doctor_speech, find_sign_video
from dataset.validate_dataset import get_dataset_status

# Page Configuration
st.set_page_config(
    page_title="SignBridge | Reverse ISL",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Premium Healthcare Aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f766e 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .main-title {
        font-size: 2.6rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        background: linear-gradient(90deg, #ffffff, #5eead4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .main-subtitle {
        font-size: 1.15rem;
        color: #94a3b8;
        margin-top: 0.4rem;
        font-weight: 400;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0.9rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .status-ready {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-listening {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        animation: pulse 1.5s infinite;
    }

    .status-processing {
        background-color: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    .card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    .dark-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 1.5rem;
        color: #f8fafc;
        margin-bottom: 1.5rem;
    }

    .sign-chip {
        display: inline-block;
        background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1.1rem;
        margin-right: 0.5rem;
        box-shadow: 0 2px 4px rgba(13, 148, 136, 0.3);
    }

    .disclaimer-box {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 1rem 1.25rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.875rem;
        color: #92400e;
        margin-top: 2rem;
    }

    .metric-bubble {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "speech_status" not in st.session_state:
    st.session_state["speech_status"] = "READY"
if "recognized_text" not in st.session_state:
    st.session_state["recognized_text"] = ""
if "processed_result" not in st.session_state:
    st.session_state["processed_result"] = None
if "last_error" not in st.session_state:
    st.session_state["last_error"] = None


# Header
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h1 class="main-title">SignBridge</h1>
            <div class="main-subtitle">Doctor &rarr; Patient &bull; Reverse Indian Sign Language (ISL) System</div>
        </div>
        <div style="text-align: right; margin-top: 0.5rem;">
            <span style="background: rgba(255,255,255,0.15); padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.85rem; letter-spacing: 0.05em;">
                INCLUDE DATASET &bull; AI4BHARAT
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# Sidebar - Dataset Status & Controls
with st.sidebar:
    st.markdown("### 📊 Dataset Status")
    st.caption("AI4Bharat INCLUDE (IIT Madras)")
    
    dataset_status = get_dataset_status()
    total_classes = len(dataset_status)
    valid_classes = sum(1 for s in dataset_status.values() if s["status"] == "valid")
    total_videos = sum(s["count"] for s in dataset_status.values())
    
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        st.metric("Required Signs", f"{valid_classes}/{total_classes}")
    with col_sb2:
        st.metric("Total Videos", total_videos)
        
    st.markdown("---")
    st.markdown("#### Controlled Classes")
    for key, stat in dataset_status.items():
        name = stat["folder_name"]
        cnt = stat["count"]
        if stat["status"] == "valid":
            st.markdown(f"🟢 **{name}** &nbsp;`{cnt} videos`")
        elif stat["status"] == "empty":
            st.markdown(f"🟡 **{name}** &nbsp;*(empty folder)*")
        else:
            st.markdown(f"🔴 **{name}** &nbsp;*(not found)*")
            
    if valid_classes < total_classes:
        st.warning("⚠️ Some videos are missing. Run download script:")
        st.code("python member3/dataset/download_required_data.py --sample 2", language="bash")
        
    st.markdown("---")
    st.markdown("### ⚙️ System Settings")
    auto_replay = st.checkbox("Auto-replay video", value=False)
    st.markdown("---")
    st.caption("SignBridge Hackathon &bull; Member 3 Module")


# Main Layout: 2 Columns (Left: Doctor Input & Status | Right: Patient ISL Screen)
col_doctor, col_patient = st.columns([1, 1], gap="large")

# -------------------------------------------------------------
# COLUMN 1: DOCTOR INPUT & SPEECH RECOGNITION
# -------------------------------------------------------------
with col_doctor:
    st.markdown("### 🩺 Doctor Input")
    st.caption("Speak into the microphone or test with preset phrases.")
    
    # Status Banner
    status_class = "status-ready"
    if st.session_state["speech_status"] == "LISTENING...":
        status_class = "status-listening"
    elif st.session_state["speech_status"] == "PROCESSING...":
        status_class = "status-processing"
        
    st.markdown(f"""
    <div style="margin-bottom: 1.25rem;">
        <span class="status-badge {status_class}">
            &bull; STATUS: {st.session_state["speech_status"]}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Microphone Trigger Button
    listen_clicked = st.button("🎤 Start Listening", type="primary", use_container_width=True)
    
    if listen_clicked:
        st.session_state["speech_status"] = "LISTENING..."
        st.session_state["last_error"] = None
        
        status_placeholder = st.empty()
        status_placeholder.info("🎙️ Listening for doctor's speech... (speak now)")
        
        # Audio capture & recognition
        audio_result = listen_to_doctor(timeout=5.0, phrase_time_limit=8.0)
        
        if audio_result["success"]:
            st.session_state["speech_status"] = "PROCESSING..."
            status_placeholder.success("Speech captured successfully! Matching sign...")
            time.sleep(0.3)
            
            raw_text = audio_result["raw_text"]
            st.session_state["recognized_text"] = raw_text
            st.session_state["processed_result"] = process_doctor_speech(raw_text)
            st.session_state["speech_status"] = "READY"
            status_placeholder.empty()
            st.rerun()
        else:
            st.session_state["speech_status"] = "READY"
            st.session_state["last_error"] = audio_result["error"]
            status_placeholder.error(f"Speech recognition: {audio_result['error']}")

    if st.session_state["last_error"]:
        st.error(f"⚠️ {st.session_state['last_error']}")

    st.markdown("---")
    
    # Manual Text Input (Robust Fallback)
    st.markdown("#### ⌨️ Manual Speech Simulation")
    manual_text = st.text_input(
        "Type doctor's statement:",
        placeholder="e.g., 'Are you sick?' or 'Go to hospital tomorrow.'",
        label_visibility="collapsed"
    )
    if st.button("Process Text", use_container_width=True):
        if manual_text.strip():
            st.session_state["recognized_text"] = manual_text.strip()
            st.session_state["processed_result"] = process_doctor_speech(manual_text)
            st.session_state["speech_status"] = "READY"
            st.rerun()

    # ---------------------------------------------------------
    # DEMO MODE (Section 14)
    # ---------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🎯 Demo / Testing Mode")
    st.caption("Fail-safe demonstration mode for hackathon presentation without microphone.")
    
    demo_tab1, demo_tab2 = st.tabs(["Single Signs", "Healthcare Phrases"])
    
    with demo_tab1:
        sign_options = [
            ("Doctor", "doctor"),
            ("Patient", "patient"),
            ("Hospital", "hospital"),
            ("Medicine", "medicine"),
            ("Sick", "sick"),
            ("Healthy", "healthy"),
            ("Today", "today"),
            ("Tomorrow", "tomorrow")
        ]
        selected_sign_tuple = st.selectbox(
            "Select sign:",
            sign_options,
            format_func=lambda x: f"Sign: {x[0]}"
        )
        if st.button("▶ Play Selected Sign", use_container_width=True):
            st.session_state["recognized_text"] = selected_sign_tuple[0]
            st.session_state["processed_result"] = process_doctor_speech(selected_sign_tuple[0])
            st.rerun()

    with demo_tab2:
        preset_phrases = [
            "Are you sick?",
            "Are you healthy?",
            "Go to hospital tomorrow.",
            "Take the medicine today.",
            "Doctor is examining the patient.",
            "Hospital",
            "Medicine"
        ]
        chosen_phrase = st.selectbox("Select preset healthcare phrase:", preset_phrases)
        if st.button("▶ Play Preset Phrase", use_container_width=True):
            st.session_state["recognized_text"] = chosen_phrase
            st.session_state["processed_result"] = process_doctor_speech(chosen_phrase)
            st.rerun()


# -------------------------------------------------------------
# COLUMN 2: PATIENT SCREEN & ISL VIDEO PLAYER
# -------------------------------------------------------------
with col_patient:
    st.markdown("### 🤟 Patient ISL Display")
    st.caption("Visual Indian Sign Language translation screen for the patient.")
    
    res = st.session_state["processed_result"]
    
    if res and st.session_state["recognized_text"]:
        st.markdown(f"""
        <div style="background: #f1f5f9; padding: 1rem 1.25rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid #0f766e;">
            <div style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase;">Doctor Said</div>
            <div style="font-size: 1.25rem; font-weight: 600; color: #0f172a; margin-top: 0.2rem;">
                "{st.session_state['recognized_text']}"
            </div>
            <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.3rem;">
                Normalized: <code>{res['recognized_text']}</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        matched_signs = res.get("matched_signs", [])
        
        if not matched_signs:
            st.warning(
                "ℹ️ No approved ISL signs detected in the doctor's speech.\n\n"
                "Controlled vocabulary: `doctor`, `patient`, `hospital`, `medicine`, `sick`, `healthy`, `today`, `tomorrow`."
            )
        else:
            # Display chips for recognized signs
            st.markdown("#### Recognized ISL Signs:")
            chip_html = " ".join([
                f'<span class="sign-chip">{s["sign"].capitalize()} <small>({s["dataset_label"]})</small></span>'
                for s in matched_signs
            ])
            st.markdown(f'<div style="margin-bottom: 1.25rem;">{chip_html}</div>', unsafe_allow_html=True)
            
            # Display Videos
            if len(matched_signs) == 1:
                sign_info = matched_signs[0]
                video_rel_path = sign_info["video_path"]
                
                if video_rel_path:
                    video_abs_path = MEMBER3_DIR / video_rel_path
                    if video_abs_path.exists():
                        st.video(str(video_abs_path), format="video/mp4")
                        st.caption(f"📁 Video: `{video_rel_path}` &bull; Dataset Class: **{sign_info['dataset_label']}**")
                    else:
                        st.error(f"⚠️ Video file `{video_rel_path}` not found on disk.")
                else:
                    st.error(f"⚠️ Video data not found for sign **{sign_info['sign']}**. Please run dataset download script.")
            else:
                # Multi-Sign Sentence (Section 10 & 13)
                st.info(f"Detected **{len(matched_signs)} signs** in spoken sequence:")
                
                sign_tabs = st.tabs([f"Sign {i+1}: {s['sign'].capitalize()}" for i, s in enumerate(matched_signs)])
                for idx, (tab, sign_info) in enumerate(zip(sign_tabs, matched_signs)):
                    with tab:
                        st.markdown(f"**ISL Sign {idx+1}:** `{sign_info['dataset_label']}`")
                        video_rel_path = sign_info["video_path"]
                        if video_rel_path:
                            video_abs_path = MEMBER3_DIR / video_rel_path
                            if video_abs_path.exists():
                                st.video(str(video_abs_path), format="video/mp4")
                                st.caption(f"📁 Video: `{video_rel_path}`")
                            else:
                                st.error(f"⚠️ Video file `{video_rel_path}` not found on disk.")
                        else:
                            st.error(f"⚠️ Video data not found for **{sign_info['sign']}**.")

    else:
        # Default placeholder screen
        st.markdown("""
        <div style="border: 2px dashed #cbd5e1; border-radius: 14px; padding: 4rem 2rem; text-align: center; color: #94a3b8;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🤟</div>
            <div style="font-size: 1.25rem; font-weight: 600; color: #475569;">Ready for Doctor Speech</div>
            <div style="font-size: 0.95rem; margin-top: 0.5rem;">
                Click <b>🎤 Start Listening</b> or choose a phrase from <b>🎯 Demo Mode</b> to display ISL translation videos.
            </div>
        </div>
        """, unsafe_allow_html=True)


# Medical Safety Disclaimer (Section 21)
st.markdown(f"""
<div class="disclaimer-box">
    <strong>⚠️ Medical Safety & Clinical Protocol Notice:</strong><br>
    {MEDICAL_SAFETY_DISCLAIMER}
</div>
""", unsafe_allow_html=True)
