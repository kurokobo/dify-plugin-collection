from typing import Any

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
            self._validate_openai_credentials(api_key, base_url_v1)
        elif service == "azure_openai":
            if not base_url:
                raise ToolProviderCredentialValidationError("API Base URL is required for Azure OpenAI")
            self._validate_azure_openai_credentials(api_key, base_url, model)
        else:
            raise ToolProviderCredentialValidationError(f"Unsupported service: {service}")

    def _validate_openai_credentials(self, api_key: str, base_url: str | None) -> None:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        try:
            client.models.list()
        except openai.AuthenticationError:
            raise ToolProviderCredentialValidationError("Invalid OpenAI API key")
        except Exception as exc:  # noqa: BLE001
            raise ToolProviderCredentialValidationError(f"Error validating OpenAI API key: {str(exc)}")

    def _validate_azure_openai_credentials(self, api_key: str, base_url: str, model: str) -> None:
        client = openai.AzureOpenAI(api_key=api_key, api_version="2025-04-01-preview", azure_endpoint=base_url)
        try:
            client.models.list()
        except openai.AuthenticationError:
            raise ToolProviderCredentialValidationError("Invalid Azure OpenAI API key")
        except Exception as exc:  # noqa: BLE001
            raise ToolProviderCredentialValidationError(f"Error validating Azure OpenAI API key: {str(exc)}")
