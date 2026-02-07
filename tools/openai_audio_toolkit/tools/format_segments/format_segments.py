from collections.abc import Generator
from typing import Any
import logging
import json

from dify_plugin import Tool
from dify_plugin.config.logger_format import plugin_logger_handler
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.utils.segment_utils import format_segments_payload, normalize_segments_payload


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class FormatSegmentsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            logger.info("Tool invoked: format_segments")

            segments_json_string = tool_parameters.get("segments_json_string")
            output_format = tool_parameters.get("output_format") or "plain_text"

            if not segments_json_string:
                raise ToolProviderCredentialValidationError("segments_json_string is required")

            try:
                payload = normalize_segments_payload(segments_json_string)
            except ValueError as exc:
                raise ToolProviderCredentialValidationError(str(exc))

            if output_format in {"json_text", "json_file"}:
                json_text = json.dumps(payload, ensure_ascii=False)
                if output_format == "json_file":
                    logger.info("Yielding formatted JSON file")
                    yield self.create_blob_message(
                        (json_text + "\n").encode("utf-8"),
                        meta={
                            "filename": "segments.json",
                            "mime_type": "application/json",
                        },
                    )
                else:
                    logger.info("Yielding formatted JSON text")
                    yield self.create_text_message(json_text)
            else:
                formatted, mime_type, file_extension = format_segments_payload(payload, output_format)
                if output_format.endswith("_file"):
                    filename = f"transcript.{file_extension}"
                    logger.info("Yielding formatted file")
                    yield self.create_blob_message(
                        formatted.encode("utf-8"),
                        meta={
                            "filename": filename,
                            "mime_type": mime_type,
                        },
                    )
                else:
                    logger.info("Yielding formatted text")
                    yield self.create_text_message(formatted)

        except ToolProviderCredentialValidationError as e:
            error_msg = f"Error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise ToolProviderCredentialValidationError(error_msg)
