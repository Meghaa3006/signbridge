"""
Download and Extraction Script for SignBridge Member 3.

Selectively downloads and extracts ONLY the 8 required ISL healthcare categories
from the AI4Bharat / IIT Madras INCLUDE dataset on Zenodo (Record 4010759).

Required Categories:
  1. Doctor    -> '87. Doctor'    (Archive: Jobs_1of2.zip)
  2. Patient   -> '88. Patient'   (Archive: Jobs_1of2.zip)
  3. Hospital  -> '30. Hospital'  (Archive: Places_3of4.zip)
  4. Medicine  -> '3. Medicine'   (Archive: Society_1of3.zip)
  5. sick      -> '98. sick'      (Archive: Adjectives_8of8.zip)
  6. healthy   -> '99. healthy'   (Archive: Adjectives_8of8.zip)
  7. Today     -> '73. Today'     (Archive: Days_and_Time_1of3.zip)
  8. Tomorrow  -> '74. Tomorrow'  (Archive: Days_and_Time_2of3.zip)

Features:
  - Fast Single-Request Video Extraction: Reads the Central Directory remotely,
    then fetches each selected video in a single contiguous HTTP Range request.
    Downloads and decompresses only the required authentic .MOV files without
    saving or downloading gigabytes of unused zip archives.
  - Safe against rate-limits and timeouts.
  - Configurable sample limit (--sample N, default: 2; or --all for entire set).
"""

import sys
import os
import argparse
import urllib.request
import io
import zipfile
import zlib
from pathlib import Path

# Add member3 root to path
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

from config import CONTROLLED_VOCABULARY, VIDEOS_DIR, ZENODO_BASE_FILES_URL


class ZipCDReader(io.RawIOBase):
    """
    In-memory virtual zip stream holding only the Central Directory and EOCD.
    Allows zipfile.ZipFile to parse all file metadata with zero video data fetched.
    """
    def __init__(self, cd_offset: int, cd_bytes: bytes, eocd_bytes: bytes, file_len: int):
        self.cd_offset = cd_offset
        self.cd_bytes = cd_bytes
        self.eocd_bytes = eocd_bytes
        self.file_len = file_len
        self.pos = 0

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        elif whence == io.SEEK_END:
            self.pos = self.file_len + offset
        return self.pos

    def tell(self) -> int:
        return self.pos

    def readinto(self, b) -> int:
        sz = len(b)
        if self.cd_offset <= self.pos < self.cd_offset + len(self.cd_bytes):
            start = self.pos - self.cd_offset
            data = self.cd_bytes[start : start + sz]
            b[:len(data)] = data
            self.pos += len(data)
            return len(data)
        
        eocd_offset = self.file_len - len(self.eocd_bytes)
        if self.pos >= eocd_offset:
            start = self.pos - eocd_offset
            data = self.eocd_bytes[start : start + sz]
            b[:len(data)] = data
            self.pos += len(data)
            return len(data)
        return 0


def get_remote_zipfile(archive_name: str):
    """
    Connects to Zenodo archive and parses its central directory in 2 fast requests.
    Returns (zipfile.ZipFile, archive_url).
    """
    archive_url = f"{ZENODO_BASE_FILES_URL}/{archive_name}/content"
    req = urllib.request.Request(archive_url, method="HEAD", headers={"User-Agent": "SignBridge/1.0"})
    with urllib.request.urlopen(req) as resp:
        file_len = int(resp.headers["Content-Length"])

    # Read last 256KB to locate EOCD
    tail_size = min(262144, file_len)
    req = urllib.request.Request(
        archive_url,
        headers={"Range": f"bytes={file_len - tail_size}-{file_len - 1}", "User-Agent": "SignBridge/1.0"}
    )
    with urllib.request.urlopen(req) as resp:
        tail_bytes = resp.read()

    eocd_pos = tail_bytes.rfind(b"PK\x05\x06")
    if eocd_pos == -1:
        raise ValueError(f"Could not locate EOCD in {archive_name}")

    cd_size = int.from_bytes(tail_bytes[eocd_pos + 12 : eocd_pos + 16], "little")
    cd_offset = int.from_bytes(tail_bytes[eocd_pos + 16 : eocd_pos + 20], "little")

    # Fetch Central Directory
    req = urllib.request.Request(
        archive_url,
        headers={"Range": f"bytes={cd_offset}-{cd_offset + cd_size - 1}", "User-Agent": "SignBridge/1.0"}
    )
    with urllib.request.urlopen(req) as resp:
        cd_bytes = resp.read()

    reader = ZipCDReader(cd_offset, cd_bytes, tail_bytes[eocd_pos:], file_len)
    zf = zipfile.ZipFile(reader)
    return zf, archive_url


def extract_single_video(archive_url: str, info: zipfile.ZipInfo, dest_path: Path):
    """
    Downloads a single video file in one Range request and decompresses it to dest_path.
    """
    # Read local header to determine exact data offset (local header = 30 bytes + fn_len + extra_len)
    req = urllib.request.Request(
        archive_url,
        headers={"Range": f"bytes={info.header_offset}-{info.header_offset + 30 + 300}", "User-Agent": "SignBridge/1.0"}
    )
    with urllib.request.urlopen(req) as resp:
        lh = resp.read()

    fn_len = int.from_bytes(lh[26:28], "little")
    extra_len = int.from_bytes(lh[28:30], "little")
    data_offset = info.header_offset + 30 + fn_len + extra_len

    # Fetch compressed data in one contiguous request
    req = urllib.request.Request(
        archive_url,
        headers={
            "Range": f"bytes={data_offset}-{data_offset + info.compress_size - 1}",
            "User-Agent": "SignBridge/1.0"
        }
    )
    with urllib.request.urlopen(req) as resp:
        comp_data = resp.read()

    # Decompress
    if info.compress_type == zipfile.ZIP_DEFLATED:
        uncomp = zlib.decompress(comp_data, -15)
    else:
        uncomp = comp_data

    # Write to destination
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(".tmp")
    with open(temp_path, "wb") as f:
        f.write(uncomp)
    temp_path.replace(dest_path)


def download_category_videos(archive_name: str, target_specs: list, sample_limit: int | None = 2):
    """
    Downloads videos for target categories located inside the specified archive.
    """
    print(f"\n[Connecting] Accessing {archive_name} Central Directory...", flush=True)
    try:
        zf, archive_url = get_remote_zipfile(archive_name)
    except Exception as e:
        print(f"Error accessing archive {archive_name}: {e}", flush=True)
        return

    all_names = zf.namelist()

    for spec in target_specs:
        prefix = spec["archive_path_prefix"]
        folder_name = spec["folder_name"]
        dest_dir = VIDEOS_DIR / folder_name
        dest_dir.mkdir(parents=True, exist_ok=True)

        matching_entries = [
            n for n in all_names
            if n.startswith(prefix) and not n.endswith('/') and '.' in n
        ]

        if sample_limit is not None and sample_limit > 0:
            matching_entries = matching_entries[:sample_limit]

        print(f"  -> Category '{folder_name}' ({spec['dataset_label']}): {len(matching_entries)} videos planned.", flush=True)

        for idx, entry_name in enumerate(matching_entries, 1):
            file_basename = Path(entry_name).name
            dest_file = dest_dir / file_basename

            if dest_file.exists() and dest_file.stat().st_size > 0:
                print(f"     [{idx}/{len(matching_entries)}] Already exists: {file_basename} ({dest_file.stat().st_size / (1024*1024):.2f} MB)", flush=True)
                continue

            info = zf.getinfo(entry_name)
            expected_mb = info.file_size / (1024 * 1024)
            print(f"     [{idx}/{len(matching_entries)}] Downloading {file_basename} ({expected_mb:.2f} MB)...", end="", flush=True)
            try:
                extract_single_video(archive_url, info, dest_file)
                print(f" done ✓", flush=True)
            except Exception as ex:
                print(f" FAILED: {ex}", flush=True)


def download_and_extract_all(sample_limit: int | None = 2):
    """
    Downloads required videos across all 6 INCLUDE archives.
    """
    print("=" * 65)
    print("SignBridge Member 3 - High-Speed Selective Dataset Downloader")
    print(f"Target Destination: {VIDEOS_DIR}")
    print(f"Mode: {'ALL available videos' if sample_limit is None else f'{sample_limit} videos per category'}")
    print("=" * 65)

    archives_map = {}
    for key, spec in CONTROLLED_VOCABULARY.items():
        arch = spec["archive"]
        if arch not in archives_map:
            archives_map[arch] = []
        archives_map[arch].append(spec)

    print(f"Identified 6 source archives out of 43 in INCLUDE:")
    for arch, specs in archives_map.items():
        classes_str = ", ".join(f"{s['folder_name']} ({s['dataset_label']})" for s in specs)
        print(f"  • {arch} -> [{classes_str}]")

    for arch, specs in archives_map.items():
        download_category_videos(arch, specs, sample_limit=sample_limit)

    print("\n" + "=" * 65)
    print("Selective download process completed.")
    print("=" * 65)

    from dataset.validate_dataset import validate_dataset
    validate_dataset()


def main():
    parser = argparse.ArgumentParser(
        description="Selectively download only required Member 3 ISL categories from Zenodo INCLUDE dataset."
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=2,
        help="Number of videos per category (default: 2 for rapid hackathon setup). Set to 0 or use --all for complete set."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available videos for the 8 required categories (approx 132 videos total, ~1.4 GB)."
    )

    args = parser.parse_args()
    limit = None if args.all or args.sample <= 0 else args.sample
    download_and_extract_all(sample_limit=limit)


if __name__ == "__main__":
    main()
