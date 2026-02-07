from collections.abc import Generator
from typing import Any
import logging

from dify_plugin import Tool
from dify_plugin.config.logger_format import plugin_logger_handler
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.utils.audio_io import split_audio_files


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class SplitAudioTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        input_files = tool_parameters.get("input_files", [])
        if not input_files:
            yield self.create_text_message("No input files provided")
            return

        use_silence_detection = tool_parameters.get("use_silence_detection", False)

        try:
            logger.info("Tool invoked: split_audio")
            logger.info("Processing %s input file(s)", len(input_files))
            logger.info("Silence detection: %s", "enabled" if use_silence_detection else "disabled")

            output_files = split_audio_files(
                input_files,
                use_silence_detection=use_silence_detection,
                logger=logger,
            )
            if not output_files:
                yield self.create_text_message("No audio files could be processed")
                return

            # Return all audio files
            for file_index, item in enumerate(output_files, start=1):
                logger.info("Yielding file %s of %s", file_index, len(output_files))
                yield self.create_blob_message(
                    item.data,
                    meta={
                        "filename": item.filename,
                        "mime_type": item.mime_type,
                    },
                )

        except ToolProviderCredentialValidationError as e:
            error_msg = f"Error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise ToolProviderCredentialValidationError(error_msg)
