from typing import Any
import requests

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class FileToolsProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        api_base_url = credentials.get("api_base_url")
        api_key = credentials.get("api_key")
        if not api_base_url:
            raise ToolProviderCredentialValidationError("Knowledge API base URL is required.")
        if not api_key:
            raise ToolProviderCredentialValidationError("Knowledge API key is required.")

        # get knowledge base list to validate API base URL and key
        headers = {
            "authorization": f"bearer {api_key}",
            "content-type": "application/json",
        }
        url = f"{api_base_url.rstrip('/')}/datasets"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            _ = response.json()
        except Exception as e:
            raise ToolProviderCredentialValidationError(f"Failed to validate API credentials: {str(e)}")
