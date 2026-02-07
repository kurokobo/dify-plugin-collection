from collections.abc import Generator
from typing import Any
import logging
import json

from dify_plugin import Tool
from dify_plugin.config.logger_format import plugin_logger_handler
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.utils.segment_utils import parse_segments_payload, format_timestamp_hhmmss


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


def _normalize_preview_limit(value: Any) -> int:
    if value is None or value == "":
        return 0

    try:
        limit = int(float(value))
    except (TypeError, ValueError):
        raise ToolProviderCredentialValidationError("preview_limit must be an integer")

    if limit < 0:
        raise ToolProviderCredentialValidationError("preview_limit must be 0 or a positive integer")

    return limit


def _parse_segments_payload(tool_parameters: dict[str, Any]) -> dict[str, Any]:
    segments_json_string = tool_parameters.get("segments_json_string")
    segments_json_file = tool_parameters.get("segments_json_file")

    try:
        return parse_segments_payload(segments_json_string, segments_json_file)
    except ValueError as exc:
        raise ToolProviderCredentialValidationError(str(exc))


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _format_transcript_entry(entry: Any) -> str:
    if isinstance(entry, dict):
        text = (entry.get("text") or "").strip()
        start = _safe_float(entry.get("start", 0.0))
        timestamp = format_timestamp_hhmmss(start)
    else:
        text = str(entry).strip()
        timestamp = format_timestamp_hhmmss(0.0)
    return f"[{timestamp}] {text}" if text else f"[{timestamp}]"


def _group_segments_by_speaker(payload: dict[str, Any]) -> list[dict[str, Any]]:
    segments = payload.get("segments", [])
    if not isinstance(segments, list):
        raise ToolProviderCredentialValidationError("segments must be an array")

    speakers: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []

    for segment in segments:
        if not isinstance(segment, dict):
            continue

        speaker = segment.get("speaker") or "Speaker"
        text = (segment.get("text") or "").strip()
        if not text:
            continue

        start = _safe_float(segment.get("start", 0.0))

        if speaker not in speakers:
            speakers[speaker] = []
            order.append(speaker)
        speakers[speaker].append(
            {
                "text": text,
                "start": start,
            }
        )

    return [
        {
            "speaker": speaker,
            "transcript": speakers[speaker],
        }
        for speaker in order
    ]


def _apply_preview_limit(items: list[dict[str, Any]], preview_limit: int) -> list[dict[str, Any]]:
    if preview_limit <= 0:
        return items

    limited: list[dict[str, Any]] = []
    for item in items:
        transcript = item.get("transcript", [])
        limited.append(
            {
                "speaker": item.get("speaker", "Speaker"),
                "transcript": transcript[:preview_limit],
            }
        )

    return limited


def _format_plain_text(items: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, item in enumerate(items):
        if index > 0:
            lines.append("")
        speaker = item.get("speaker", "Speaker")
        lines.append(f"{speaker}:")
        for entry in item.get("transcript", []):
            lines.append(_format_transcript_entry(entry))

    return "\n".join(lines).rstrip() + "\n"


def _format_markdown_list(items: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, item in enumerate(items):
        if index > 0:
            lines.append("")
        speaker = item.get("speaker", "Speaker")
        lines.append(f"#### {speaker}")
        lines.append("")
        for entry in item.get("transcript", []):
            lines.append(f"- {_format_transcript_entry(entry)}")

    return "\n".join(lines).rstrip() + "\n"


def _format_markdown_collapsible(items: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, item in enumerate(items):
        if index > 0:
            lines.append("")
        speaker = item.get("speaker", "Speaker")
        lines.append("<details>")
        lines.append(f"<summary>{speaker}</summary>")
        lines.append("")
        for entry in item.get("transcript", []):
            lines.append(f"- {_format_transcript_entry(entry)}")
        lines.append("</details>")

    return "\n".join(lines).rstrip() + "\n"


class ReviewSpeakersTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            logger.info("Tool invoked: review_speakers")

            output_format = tool_parameters.get("output_format") or "plain_text"
            preview_limit = _normalize_preview_limit(tool_parameters.get("preview_limit"))

            payload = _parse_segments_payload(tool_parameters)
            grouped = _group_segments_by_speaker(payload)
            grouped = _apply_preview_limit(grouped, preview_limit)

            if output_format in {"json_text", "json_file"}:
                json_text = json.dumps({"speakers": grouped}, ensure_ascii=False)
                if output_format == "json_file":
                    logger.info("Yielding grouped JSON file")
                    yield self.create_blob_message(
                        (json_text + "\n").encode("utf-8"),
                        meta={
                            "filename": "speaker_groups.json",
                            "mime_type": "application/json",
                        },
                    )
                else:
                    logger.info("Yielding grouped JSON text")
                    yield self.create_text_message(json_text)
                return

            if output_format in {"plain_text", "plain_file"}:
                formatted = _format_plain_text(grouped)
                mime_type = "text/plain"
                file_extension = "txt"
            elif output_format in {"markdown_list_text", "markdown_list_file"}:
                formatted = _format_markdown_list(grouped)
                mime_type = "text/markdown"
                file_extension = "md"
            elif output_format in {"markdown_collapsible_text", "markdown_collapsible_file"}:
                formatted = _format_markdown_collapsible(grouped)
                mime_type = "text/markdown"
                file_extension = "md"
            else:
                raise ToolProviderCredentialValidationError(
                    "output_format must be one of plain_*, json_*, markdown_list_*, markdown_collapsible_*"
                )

            if output_format.endswith("_file"):
                filename = f"speaker_groups.{file_extension}"
                logger.info("Yielding grouped file")
                yield self.create_blob_message(
                    formatted.encode("utf-8"),
                    meta={
                        "filename": filename,
                        "mime_type": mime_type,
                    },
                )
            else:
                logger.info("Yielding grouped text")
                yield self.create_text_message(formatted)

        except ToolProviderCredentialValidationError as e:
            error_msg = f"Error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise ToolProviderCredentialValidationError(error_msg)
