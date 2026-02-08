from collections.abc import Generator
from typing import Any
import logging
import json

from dify_plugin import Tool
from dify_plugin.config.logger_format import plugin_logger_handler
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.utils.segment_utils import parse_segments_payload


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


def _parse_segments_payload(tool_parameters: dict[str, Any]) -> dict[str, Any]:
    segments_json_string = tool_parameters.get("segments_json_string")
    segments_json_file = tool_parameters.get("segments_json_file")

    try:
        return parse_segments_payload(segments_json_string, segments_json_file)
    except ValueError as exc:
        raise ToolProviderCredentialValidationError(str(exc))


def _parse_replace_rules(rules_text: Any) -> dict[str, str]:
    if rules_text is None or str(rules_text).strip() == "":
        raise ToolProviderCredentialValidationError("replace_rules is required")

    rules: dict[str, str] = {}
    for line_number, raw_line in enumerate(str(rules_text).splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            raise ToolProviderCredentialValidationError(
                f"Invalid rule at line {line_number}: missing ':' separator"
            )

        from_speaker, _, to_speaker = line.partition(":")
        from_speaker = from_speaker.strip()
        to_speaker = to_speaker.strip()

        if not from_speaker or not to_speaker:
            raise ToolProviderCredentialValidationError(
                f"Invalid rule at line {line_number}: both sides are required"
            )

        rules[from_speaker] = to_speaker

    if not rules:
        raise ToolProviderCredentialValidationError("replace_rules must include at least one rule")

    return rules


def _apply_replace_rules(payload: dict[str, Any], rules: dict[str, str]) -> dict[str, Any]:
    segments = payload.get("segments", [])
    if not isinstance(segments, list):
        raise ToolProviderCredentialValidationError("segments must be an array")

    for segment in segments:
        if not isinstance(segment, dict):
            continue
        speaker = segment.get("speaker")
        if speaker in rules:
            segment["speaker"] = rules[speaker]

    return payload


class ReplaceSpeakerNameTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            logger.info("Tool invoked: replace_speaker_name")

            rules = _parse_replace_rules(tool_parameters.get("replace_rules"))

            payload = _parse_segments_payload(tool_parameters)
            payload = _apply_replace_rules(payload, rules)

            json_text = json.dumps(payload, ensure_ascii=False)

            logger.info("Yielding replaced JSON text")
            yield self.create_text_message(json_text)
            logger.info("Yielding replaced JSON message")
            yield self.create_json_message(payload)

        except ToolProviderCredentialValidationError as e:
            error_msg = f"Error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise ToolProviderCredentialValidationError(error_msg)
