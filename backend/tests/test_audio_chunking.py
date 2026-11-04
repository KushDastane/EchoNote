import pytest
from app.utils.audio_chunking import compute_chunk_windows, merge_chunk_segments
from app.utils.timestamps import format_timestamp, parse_timestamp

def test_timestamps_formatting():
    assert format_timestamp(0) == "00:00"
    assert format_timestamp(65) == "01:05"
    assert format_timestamp(3665) == "01:01:05"
    assert format_timestamp(None) == "00:00"

def test_timestamps_parsing():
    assert parse_timestamp("01:05") == 65.0
    assert parse_timestamp("01:01:05") == 3665.0
    assert parse_timestamp("") == 0.0

def test_compute_chunk_windows_short_audio():
    # Audio shorter than chunk length should produce exactly 1 window
    windows = compute_chunk_windows(total_duration_sec=120.0, chunk_length_sec=600.0, overlap_sec=10.0)
    assert len(windows) == 1
    assert windows[0]["start"] == 0.0
    assert windows[0]["end"] == 120.0
    assert windows[0]["offset"] == 0.0

def test_compute_chunk_windows_long_audio():
    # 1500 seconds (~25 mins) with 600s chunk and 10s overlap
    windows = compute_chunk_windows(total_duration_sec=1500.0, chunk_length_sec=600.0, overlap_sec=10.0)
    assert len(windows) >= 3
    assert windows[0]["start"] == 0.0
    assert windows[0]["end"] == 600.0
    # Next starts with overlap: 600 - 10 = 590
    assert windows[1]["start"] == 590.0

def test_merge_chunk_segments_offset_and_deduplication():
    # Chunk 0: offset 0
    chunk0_segments = [
        {"start": 0.0, "end": 10.0, "text": "Segment one", "speaker": "Speaker 1"},
        {"start": 590.0, "end": 598.0, "text": "Overlapping boundary segment", "speaker": "Speaker 2"}
    ]
    # Chunk 1: offset 590.0
    chunk1_segments = [
        # Duplicate in overlap window
        {"start": 0.0, "end": 8.0, "text": "Overlapping boundary segment", "speaker": "Speaker 2"},
        # New subsequent segment
        {"start": 12.0, "end": 20.0, "text": "New discussion in chunk two", "speaker": "Speaker 1"}
    ]

    merged = merge_chunk_segments([
        (0.0, chunk0_segments),
        (590.0, chunk1_segments)
    ], overlap_sec=10.0)

    # The duplicated overlapping segment should be merged/deduplicated
    texts = [m["text"] for m in merged]
    assert "Segment one" in texts
    assert "New discussion in chunk two" in texts
    assert texts.count("Overlapping boundary segment") == 1
    # Global timestamp offset applied for chunk 1
    new_seg = [m for m in merged if m["text"] == "New discussion in chunk two"][0]
    assert new_seg["start_time"] == 602.0  # 590 + 12
