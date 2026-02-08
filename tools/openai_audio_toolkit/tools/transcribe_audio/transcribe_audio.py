from collections.abc import Generator
from typing import Any
import logging

from dify_plugin import Tool
from dify_plugin.config.logger_format import plugin_logger_handler
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.utils.transcribe_utils import create_openai_client, transcribe_text_files


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class TranscribeAudioTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            input_files = tool_parameters.get("input_files")
            if not input_files:
                raise ToolProviderCredentialValidationError("Input file(s) are required")
            if not self.runtime or not self.runtime.credentials:
                raise ToolProviderCredentialValidationError("Tool runtime or credentials are missing")

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

            logger.info("Tool invoked: transcribe_audio")
            logger.info("Starting transcription with %s", service.replace("_", " ").title())
            logger.info("Processing %s file(s)", len(input_files))

            client = create_openai_client(service, api_key, base_url)
            text = transcribe_text_files(client, model, input_files, logger)

            if not text:
                raise ToolProviderCredentialValidationError("No transcription text was produced")

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
