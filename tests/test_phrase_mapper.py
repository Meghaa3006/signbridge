"""
Automated Unit Tests for SignBridge Member 3 (Phrase Mapper & Speech Processing).
Verifies:
  - Controlled single-sign recognition for all 8 required categories
  - Multi-sign extraction in sentence order
  - Rejection of unsupported medical / casual phrases
  - Text normalization behavior
  - Member 4 integration interface contract and safety compliance
"""

import unittest
import sys
from pathlib import Path

# Add member3 root to path
TEST_DIR = Path(__file__).resolve().parent
MEMBER3_DIR = TEST_DIR.parent
if str(MEMBER3_DIR) not in sys.path:
    sys.path.insert(0, str(MEMBER3_DIR))

from config import CONTROLLED_VOCABULARY
from speech_to_text import normalize_text
from phrase_mapper import match_sign, match_signs, process_doctor_speech, find_sign_video


class TestTextNormalization(unittest.TestCase):
    """Verifies deterministic text normalization rules."""

    def test_lowercase_conversion(self):
        self.assertEqual(normalize_text("DOCTOR"), "doctor")
        self.assertEqual(normalize_text("Hospital"), "hospital")

    def test_punctuation_removal(self):
        self.assertEqual(normalize_text("Are you sick?"), "are you sick")
        self.assertEqual(normalize_text("Take medicine, please!"), "take medicine please")
        self.assertEqual(normalize_text("Doctor... Patient?!"), "doctor patient")

    def test_whitespace_collapsing(self):
        self.assertEqual(normalize_text("  go   to   hospital   "), "go to hospital")
        self.assertEqual(normalize_text("\ntomorrow\t\n"), "tomorrow")

    def test_empty_string(self):
        self.assertEqual(normalize_text(""), "")
        self.assertEqual(normalize_text("   "), "")


class TestSingleSignMatching(unittest.TestCase):
    """Verifies exact single-sign matching against INCLUDE vocabulary."""

    def test_doctor(self):
        res = match_sign("doctor")
        self.assertTrue(res["matched"])
        self.assertEqual(res["sign"], "doctor")
        self.assertEqual(res["dataset_label"], "87. Doctor")

    def test_patient(self):
        res = match_sign("patient")
        self.assertTrue(res["matched"])
        self.assertEqual(res["sign"], "patient")
        self.assertEqual(res["dataset_label"], "88. Patient")

    def test_hospital(self):
        res = match_sign("hospital")
        self.assertTrue(res["matched"])
        self.assertEqual(res["sign"], "hospital")
        self.assertEqual(res["dataset_label"], "30. Hospital")

    def test_medicine(self):
        res = match_sign("medicine")
        self.assertTrue(res["matched"])
        self.assertEqual(res["sign"], "medicine")
        self.assertEqual(res["dataset_label"], "3. Medicine")

    def test_are_you_sick(self):
        res = match_sign("are you sick")
        self.assertTrue(res["matched"])
        self.assertEqual(res["sign"], "sick")
        self.assertEqual(res["dataset_label"], "98. sick")

    def test_are_you_healthy(self):
        res = match_sign("are you healthy")
        self.assertTrue(res["matched"])
        self.assertEqual(res["sign"], "healthy")
        self.assertEqual(res["dataset_label"], "99. healthy")

    def test_today(self):
        res = match_sign("today")
        self.assertTrue(res["matched"])
        self.assertEqual(res["sign"], "today")
        self.assertEqual(res["dataset_label"], "73. Today")

    def test_tomorrow(self):
        res = match_sign("tomorrow")
        self.assertTrue(res["matched"])
        self.assertEqual(res["sign"], "tomorrow")
        self.assertEqual(res["dataset_label"], "74. Tomorrow")

    def test_unsupported_statement(self):
        res = match_sign("what is the weather")
        self.assertFalse(res["matched"])
        self.assertIsNone(res["sign"])
        self.assertIsNone(res["video_path"])


class TestMultiSignMatching(unittest.TestCase):
    """Verifies sequential detection of multiple signs in sentence order."""

    def test_hospital_tomorrow(self):
        text = "Go to hospital tomorrow."
        signs = match_signs(text)
        sign_names = [s["sign"] for s in signs]
        self.assertEqual(sign_names, ["hospital", "tomorrow"])
        self.assertEqual(signs[0]["dataset_label"], "30. Hospital")
        self.assertEqual(signs[1]["dataset_label"], "74. Tomorrow")

    def test_medicine_today(self):
        text = "Take your medicine today."
        signs = match_signs(text)
        sign_names = [s["sign"] for s in signs]
        self.assertEqual(sign_names, ["medicine", "today"])

    def test_doctor_patient(self):
        text = "The doctor examined the patient."
        signs = match_signs(text)
        sign_names = [s["sign"] for s in signs]
        self.assertEqual(sign_names, ["doctor", "patient"])

    def test_no_duplicate_signs(self):
        text = "doctor doctor doctor"
        signs = match_signs(text)
        self.assertEqual(len(signs), 1)
        self.assertEqual(signs[0]["sign"], "doctor")


class TestMember4IntegrationInterface(unittest.TestCase):
    """Validates the Member 4 process_doctor_speech() interface."""

    def test_process_doctor_speech_success(self):
        res = process_doctor_speech("Are you sick?")
        self.assertTrue(res["success"])
        self.assertEqual(res["recognized_text"], "are you sick")
        self.assertEqual(len(res["matched_signs"]), 1)
        self.assertEqual(res["matched_signs"][0]["sign"], "sick")
        self.assertEqual(res["matched_signs"][0]["dataset_label"], "98. sick")
        self.assertIn("video_path", res["matched_signs"][0])

    def test_process_doctor_speech_multi_sign(self):
        res = process_doctor_speech("Go to hospital tomorrow.")
        self.assertTrue(res["success"])
        self.assertEqual(res["recognized_text"], "go to hospital tomorrow")
        self.assertEqual(len(res["matched_signs"]), 2)
        self.assertEqual(res["matched_signs"][0]["sign"], "hospital")
        self.assertEqual(res["matched_signs"][1]["sign"], "tomorrow")

    def test_process_doctor_speech_unsupported(self):
        res = process_doctor_speech("What is the weather outside today?")
        # 'today' is in the phrase, so 'today' is matched
        self.assertTrue(res["success"])
        self.assertEqual([s["sign"] for s in res["matched_signs"]], ["today"])

    def test_process_doctor_speech_completely_unsupported(self):
        res = process_doctor_speech("How are the clouds looking?")
        self.assertFalse(res["success"])
        self.assertEqual(len(res["matched_signs"]), 0)


class TestNoHallucinatedVideoPaths(unittest.TestCase):
    """Ensures find_sign_video never invents fake paths."""

    def test_invalid_sign_key(self):
        self.assertIsNone(find_sign_video("non_existent_sign"))

    def test_existing_video_is_real_file(self):
        # Doctor has at least 1 video already placed
        video_path = find_sign_video("doctor")
        if video_path:
            full_path = MEMBER3_DIR / video_path
            self.assertTrue(full_path.exists(), f"Path does not exist on disk: {full_path}")
            self.assertTrue(full_path.is_file())


if __name__ == "__main__":
    unittest.main()
