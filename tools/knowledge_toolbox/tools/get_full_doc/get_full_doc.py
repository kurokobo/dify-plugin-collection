from collections.abc import Generator
from typing import Any
import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class GetFullDocTool(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        knowledge_id = tool_parameters.get("knowledge_id")
        document_id = tool_parameters.get("document_id")
        delimiter = tool_parameters.get("delimiter", "\n\n").encode().decode("unicode_escape")

        if not self.runtime or not self.runtime.credentials:
            raise ToolProviderCredentialValidationError("Tool runtime or credentials are missing")

        api_base_url = self.runtime.credentials.get("api_base_url")
        api_key = self.runtime.credentials.get("api_key")

        if not api_base_url:
            raise ToolProviderCredentialValidationError("Knowledge API base URL is required.")
        if not api_key:
            raise ToolProviderCredentialValidationError("Knowledge API key is required.")

        url = f"{api_base_url.rstrip('/')}/datasets/{knowledge_id}/documents/{document_id}/segments"
        headers = {
            "authorization": f"bearer {api_key}",
            "content-type": "application/json",
        }

        all_data = []
        page = 1
        has_more = True
        params = {"limit": 100}

        try:
            while has_more:
                params["page"] = page
                response = requests.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    raise Exception(f"{response.status_code} {response.text}")
                resp_json = response.json()
                all_data.extend(resp_json.get("data", []))
                has_more = resp_json.get("has_more", False)
                page += 1
        except Exception as e:
            yield self.create_text_message(f"Error fetching segments: {str(e)}")
            return

        text = delimiter.join([segment.get("content", "")
                              for segment in all_data])
        yield self.create_text_message(text)
