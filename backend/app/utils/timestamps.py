from typing import Optional, Union

def format_timestamp(seconds: Optional[Union[float, int]]) -> str:
    """Format seconds into HH:MM:SS or MM:SS format."""
    if seconds is None or seconds < 0:
        return "00:00"
    
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def parse_timestamp(timestamp_str: Optional[str]) -> float:
    """Parse HH:MM:SS or MM:SS timestamp string to seconds."""
    if not timestamp_str or not isinstance(timestamp_str, str):
        return 0.0
    
    parts = timestamp_str.strip().split(":")
    try:
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 1:
            return float(parts[0])
    except (ValueError, TypeError):
        return 0.0
    return 0.0
