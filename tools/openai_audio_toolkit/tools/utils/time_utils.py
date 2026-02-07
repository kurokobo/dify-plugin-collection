"""
Time/offset utilities for audio segment processing
"""

from typing import Any


def adjust_segment_offsets(segments: list[dict[str, Any]], offset_seconds: float) -> None:
    """
    Adjust start and end times of segments by adding an offset (in-place).
    """
    for seg in segments:
        if "start" in seg:
            seg["start"] = float(seg["start"]) + offset_seconds
        if "end" in seg:
            seg["end"] = float(seg["end"]) + offset_seconds
