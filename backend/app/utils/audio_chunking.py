import os
from typing import List, Dict, Any, Tuple

def compute_chunk_windows(
    total_duration_sec: float,
    chunk_length_sec: float = 600.0,
    overlap_sec: float = 10.0
) -> List[Dict[str, float]]:
    """
    Computes list of chunk windows with start_time, end_time, and duration.
    For audio shorter than chunk_length_sec, returns a single window.
    Overlap allows transcript context continuity between chunks.
    """
    if total_duration_sec <= 0:
        return []

    if total_duration_sec <= chunk_length_sec:
        return [{
            "index": 0,
            "start": 0.0,
            "end": total_duration_sec,
            "duration": total_duration_sec,
            "offset": 0.0
        }]

    windows = []
    current_start = 0.0
    idx = 0
    step = max(chunk_length_sec - overlap_sec, 1.0)

    while current_start < total_duration_sec:
        current_end = min(current_start + chunk_length_sec, total_duration_sec)
        windows.append({
            "index": idx,
            "start": current_start,
            "end": current_end,
            "duration": current_end - current_start,
            "offset": current_start
        })
        idx += 1
        if current_end >= total_duration_sec:
            break
        current_start += step

    return windows

def merge_chunk_segments(
    chunked_results: List[Tuple[float, List[Dict[str, Any]]]],
    overlap_sec: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Merges transcribed segments from consecutive chunks.
    chunked_results is a list of tuples: (chunk_offset_sec, [segment_dict, ...])
    
    Each segment_dict in raw chunk output has relative 'start' and 'end'.
    We apply the offset, and filter out duplicated segments that fall inside
    the overlap transition threshold from previous chunk.
    """
    merged_segments: List[Dict[str, Any]] = []
    
    for chunk_idx, (offset, segments) in enumerate(chunked_results):
        for seg in segments:
            global_start = round(offset + seg["start"], 2)
            global_end = round(offset + seg["end"], 2)
            text = seg.get("text", "").strip()
            speaker = seg.get("speaker", "Speaker")

            if not text:
                continue

            # In overlap region of subsequent chunk, check if already covered
            if chunk_idx > 0 and global_start < offset + overlap_sec:
                # If existing last segment text closely matches or overlaps, avoid duplication
                if merged_segments:
                    last_seg = merged_segments[-1]
                    if abs(last_seg["end_time"] - global_end) < 1.0 or last_seg["text"].lower() == text.lower():
                        continue

            merged_segments.append({
                "start_time": global_start,
                "end_time": global_end,
                "speaker": speaker,
                "text": text
            })

    return merged_segments
