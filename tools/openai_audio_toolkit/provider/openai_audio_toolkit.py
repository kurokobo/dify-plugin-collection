from typing import Any
import io
import wave

from yarl import URL
import openai

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class OpenAIAudioToolkitProvider(ToolProvider):

    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        api_key = credentials.get("api_key")
        service = credentials.get("service")
        base_url = credentials.get("openai_base_url")
        model = credentials.get("model")

        if not api_key:
            raise ToolProviderCredentialValidationError("API key is missing")
        if not service:
            raise ToolProviderCredentialValidationError("Service is not specified")
        if not model:
            raise ToolProviderCredentialValidationError("Model is required")

        if service == "openai":
            base_url_v1 = str(URL(base_url) / "v1") if base_url else None
            self._validate_openai_credentials(api_key, base_url_v1, model)
        elif service == "azure_openai":
            if not base_url:
                raise ToolProviderCredentialValidationError("API Base URL is required for Azure OpenAI")
            self._validate_azure_openai_credentials(api_key, base_url, model)
        else:
            raise ToolProviderCredentialValidationError(f"Unsupported service: {service}")

    def _validate_openai_credentials(self, api_key: str, base_url: str | None, model: str) -> None:
        try:
            with openai.OpenAI(api_key=api_key, base_url=base_url, timeout=30.0, max_retries=0) as client:
                self._validate_transcription(client, model)
        except openai.AuthenticationError as exc:
            raise ToolProviderCredentialValidationError("Invalid OpenAI API key") from exc
        except openai.OpenAIError as exc:
            raise ToolProviderCredentialValidationError(f"Error validating OpenAI credentials: {str(exc)}") from exc

    def _validate_azure_openai_credentials(self, api_key: str, base_url: str, model: str) -> None:
        try:
            with openai.AzureOpenAI(
                api_key=api_key,
                api_version="2025-04-01-preview",
                azure_endpoint=base_url,
                timeout=30.0,
                max_retries=0,
            ) as client:
                self._validate_transcription(client, model)
        except openai.AuthenticationError as exc:
            raise ToolProviderCredentialValidationError("Invalid Azure OpenAI API key") from exc
        except openai.OpenAIError as exc:
            raise ToolProviderCredentialValidationError(f"Error validating Azure OpenAI credentials: {str(exc)}") from exc

    def _validate_transcription(self, client: openai.OpenAI | openai.AzureOpenAI, model: str) -> None:
        with io.BytesIO() as audio_stream:
            with wave.open(audio_stream, "wb") as audio_file:
                audio_file.setnchannels(1)
                audio_file.setsampwidth(2)
                audio_file.setframerate(16000)
                audio_file.writeframes(b"\x00\x00" * 16000)
            audio_stream.seek(0)

            client.audio.transcriptions.create(
                file=("validation.wav", audio_stream, "audio/wav"),
                model=model,
                response_format="text",
            )
