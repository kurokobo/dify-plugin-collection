"""
Segment identifier utilities
"""

from typing import Any
import json
from tools.utils.time_utils import adjust_segment_offsets


def update_segment_identifiers(segments: list[dict[str, Any]], file_index: int, chunk_index: int) -> None:
    """
    Update segment speaker, id, and other identifiers with file/chunk context.

    Args:
        segments: List of segment dictionaries to update
        file_index: 1-based file index
        chunk_index: 0 for single chunk, 1-based chunk index for split chunks
    """
    for seg in segments:
        if "speaker" in seg and seg["speaker"]:
            if chunk_index > 0:
                seg["speaker"] = f"{file_index}-{chunk_index}-{seg['speaker']}"
            else:
                seg["speaker"] = f"{file_index}-{seg['speaker']}"

        if "id" in seg:
            original_id = seg["id"]
            if chunk_index > 0:
                seg["id"] = f"file_{file_index}/chunk_{chunk_index}/{original_id}"
            else:
                seg["id"] = f"file_{file_index}/{original_id}"


def concat_segments_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    all_segments: list[dict[str, Any]] = []
    total_duration = 0.0

    for item_index, item in enumerate(items, start=1):
        segments = item.get("segments", [])
        metadata = item.get("metadata", {})

        adjust_segment_offsets(segments, total_duration)

        for segment in segments:
            if "speaker" in segment and segment["speaker"]:
                segment["speaker"] = f"{item_index}-{segment['speaker']}"
            if "id" in segment:
                segment["id"] = f"item_{item_index}/{segment['id']}"
        all_segments.extend(segments)

        item_duration = 0.0
        if isinstance(metadata, dict):
            item_duration = float(metadata.get("total_duration_sec", 0.0))
        if item_duration <= 0.0:
            if segments:
                item_duration = max(float(seg.get("end", 0.0)) for seg in segments)

        total_duration += item_duration

    return {
        "segments": all_segments,
        "metadata": {
            "total_duration_sec": total_duration,
            "item_count": len(items),
            "segment_count": len(all_segments),
        },
    }


def normalize_concat_items(items: Any) -> list[dict[str, Any]]:
    if items is None:
        raise ValueError("items is required")

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in items_json_string: {str(exc)}")

    if not isinstance(items, list):
        raise ValueError("items must be an array")

    if items and all(isinstance(item, str) for item in items):
        normalized_items: list[dict[str, Any]] = []
        for item_index, item in enumerate(items, start=1):
            try:
                parsed_item = json.loads(item)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at items[{item_index}]: {str(exc)}")
            if not isinstance(parsed_item, dict):
                raise ValueError(f"items[{item_index}] must be a JSON object")
            normalized_items.append(parsed_item)
        items = normalized_items

    for item_index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError("Each item must be an object")

        segments = item.get("segments", [])
        if not isinstance(segments, list):
            raise ValueError("segments must be an array")

    return items


def normalize_segments_payload(items: Any) -> dict[str, Any]:
    if items is None:
        raise ValueError("items is required")

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON input: {str(exc)}")

    if isinstance(items, list):
        normalized_items = normalize_concat_items(items)
        return concat_segments_items(normalized_items)

    if isinstance(items, dict):
        segments = items.get("segments", [])
        if not isinstance(segments, list):
            raise ValueError("segments must be an array")
        return items

    raise ValueError("items must be an object or array")


def parse_segments_payload(segments_json_string: Any, segments_json_file: Any) -> dict[str, Any]:
    if segments_json_string and segments_json_file:
        raise ValueError("Provide only one of segments_json_string or segments_json_file")

    if not segments_json_string and not segments_json_file:
        raise ValueError("segments_json_string or segments_json_file is required")

    if segments_json_file:
        try:
            segments_json_string = segments_json_file.blob.decode("utf-8")
        except UnicodeDecodeError:
            segments_json_string = segments_json_file.blob.decode("utf-8", errors="replace")

    return normalize_segments_payload(segments_json_string)


def _format_timestamp_vtt(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    total_sec = total_ms // 1000
    s = total_sec % 60
    total_min = total_sec // 60
    m = total_min % 60
    h = total_min // 60
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def _format_timestamp_srt(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    total_sec = total_ms // 1000
    s = total_sec % 60
    total_min = total_sec // 60
    m = total_min % 60
    h = total_min // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_timestamp_hhmmss(seconds: float) -> str:
    total_sec = int(round(seconds))
    s = total_sec % 60
    total_min = total_sec // 60
    m = total_min % 60
    h = total_min // 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_segments_payload(payload: dict[str, Any], output_format: str) -> tuple[str, str, str]:
    segments = payload.get("segments", [])
    if not isinstance(segments, list):
        raise ValueError("segments must be an array")

    normalized_format = output_format.lower()
    format_key = normalized_format.replace("_text", "").replace("_file", "")
    if format_key not in {"plain", "markdown", "vtt", "srt"}:
        raise ValueError("output_format must be one of plain_*, markdown_*, vtt_*, srt_*")

    lines: list[str] = []
    mime_type = "text/plain"
    file_extension = "txt"
    if format_key == "markdown":
        mime_type = "text/markdown"
        file_extension = "md"
    elif format_key == "vtt":
        mime_type = "text/vtt"
        file_extension = "vtt"
    elif format_key == "srt":
        mime_type = "application/x-subrip"
        file_extension = "srt"

    if format_key == "vtt":
        lines.append("WEBVTT")
        lines.append("")

    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            continue

        speaker = segment.get("speaker") or "Speaker"
        text = (segment.get("text") or "").strip()
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", 0.0))

        if format_key == "plain":
            lines.append(f"{speaker}: {text}")
        elif format_key == "markdown":
            lines.append(f"**{speaker}**: {text}  ")
        elif format_key == "vtt":
            lines.append(f"{_format_timestamp_vtt(start)} --> {_format_timestamp_vtt(end)}")
            lines.append(f"<v {speaker}>{text}</v>")
            lines.append("")
        elif format_key == "srt":
            lines.append(str(index))
            lines.append(f"{_format_timestamp_srt(start)} --> {_format_timestamp_srt(end)}")
            lines.append(f"{speaker}: {text}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n", mime_type, file_extension
