from collections.abc import Generator
from typing import Any
import logging
import json

from dify_plugin import Tool
from dify_plugin.config.logger_format import plugin_logger_handler
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.utils.segment_utils import concat_segments_items, normalize_concat_items


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class ConcatSegmentsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            logger.info("Tool invoked: concat_segments")

            items_array = tool_parameters.get("items_array")
            items_json_string = tool_parameters.get("items_json_string")

            if items_array and items_json_string:
                raise ToolProviderCredentialValidationError("Provide only one of items_array or items_json_string")

            if items_array is None and not items_json_string:
                raise ToolProviderCredentialValidationError("items_array or items_json_string is required")

            try:
                items = normalize_concat_items(items_array if items_array is not None else items_json_string)
            except ValueError as exc:
                raise ToolProviderCredentialValidationError(str(exc))

            for item_index, item in enumerate(items, start=1):
                segments = item.get("segments", [])
                logger.info("Item %s: %s segment(s)", item_index, len(segments))

            payload = concat_segments_items(items)

            logger.info("Yielding diarization result (text)")
            yield self.create_text_message(json.dumps(payload, ensure_ascii=False))
            logger.info("Yielding concatenated result")
            yield self.create_json_message(payload)

        except ToolProviderCredentialValidationError as e:
            error_msg = f"Error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise ToolProviderCredentialValidationError(error_msg)
