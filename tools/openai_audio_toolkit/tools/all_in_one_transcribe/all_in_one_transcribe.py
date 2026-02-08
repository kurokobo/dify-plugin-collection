from collections.abc import Generator
from typing import Any
import logging

from dify_plugin import Tool
from dify_plugin.config.logger_format import plugin_logger_handler
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.utils.transcribe_utils import create_openai_client, all_in_one_transcribe_files


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class AllInOneTranscribeTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            input_files = tool_parameters.get("input_files")
            if not input_files:
                raise ToolProviderCredentialValidationError("Input file(s) are required")
            if not self.runtime or not self.runtime.credentials:
                raise ToolProviderCredentialValidationError("Tool runtime or credentials are missing")

            auto_split = tool_parameters.get("auto_split", True)
            use_silence_detection = tool_parameters.get("use_silence_detection", False)
            output_format = tool_parameters.get("output_format") or "plain_text"

            credentials = self.runtime.credentials
            api_key = credentials.get("api_key")
            service = credentials.get("service")
            base_url = credentials.get("openai_base_url")
            model = credentials.get("model")
            if not api_key:
                raise ToolProviderCredentialValidationError("API key is missing")
            if not service:
                raise ToolProviderCredentialValidationError("Service is not specified")
            if not model:
                raise ToolProviderCredentialValidationError("Model is required for transcription")

            logger.info("Tool invoked: all_in_one_transcribe")
            logger.info("Starting transcription with %s", service.replace("_", " ").title())
            logger.info(
                "Processing %s file(s) with auto-split %s, silence detection %s",
                len(input_files),
                "enabled" if auto_split else "disabled",
                "enabled" if use_silence_detection else "disabled",
            )

            client = create_openai_client(service, api_key, base_url)
            text = all_in_one_transcribe_files(
                client,
                model,
                input_files,
                auto_split=auto_split,
                use_silence_detection=use_silence_detection,
                logger=logger,
            )

            if not text:
                raise ToolProviderCredentialValidationError("No transcription text was produced")

            if output_format == "plain_file":
                logger.info("Yielding transcription file")
                yield self.create_blob_message(
                    text.encode("utf-8"),
                    meta={
                        "filename": "transcript.txt",
                        "mime_type": "text/plain",
                    },
                )
            else:
                logger.info("Yielding transcription result")
                yield self.create_text_message(text)

        except ToolProviderCredentialValidationError as e:
            error_msg = f"Error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            yield self.create_text_message(error_msg)
            raise ToolProviderCredentialValidationError(error_msg)
