from collections.abc import Generator
from typing import Any
import json
import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.utils.knowledge_file_utils import KnowledgeFileClient, KnowledgeFileError


class DownloadFileTool(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        knowledge_id = tool_parameters.get("knowledge_id")
        document_id = tool_parameters.get("document_id")
        format = tool_parameters.get("format", "url")

        if not self.runtime or not self.runtime.credentials:
            raise ToolProviderCredentialValidationError("Tool runtime or credentials are missing")

        api_base_url = self.runtime.credentials.get("api_base_url")
        api_key = self.runtime.credentials.get("api_key")

        if not api_base_url:
            raise ToolProviderCredentialValidationError("Knowledge API base URL is required.")
        if not api_key:
            raise ToolProviderCredentialValidationError("Knowledge API key is required.")

        # step 1: get the file information including the download url
        client = KnowledgeFileClient(api_base_url, api_key)
        try:
            data = client.get_file_info(
                knowledge_id,
                document_id,
                with_details=format in ("json", "link", "file"),
            )
        except KnowledgeFileError as e:
            yield self.create_text_message(f"Error fetching file information: {str(e)}")
            return

        download_url = data.get("download_url")

        if format == "json":
            yield self.create_text_message(
                json.dumps(data, indent=2)
            )
            return
        elif format == "url":
            yield self.create_text_message(download_url)
            return
        elif format == "link":
            filename = data.get("name")
            markdown_link = f"[{filename}]({download_url})"
            yield self.create_text_message(markdown_link)
            return

        # step 2: fetch the file
        try:
            file_response = requests.get(download_url)
            file_response.raise_for_status()
            file_bytes = file_response.content
        except Exception as e:
            yield self.create_text_message(
                f"Error downloading file: {str(e)}"
            )
            return

        if format == "content":
            try:
                text = file_bytes.decode("utf-8")
                yield self.create_text_message(text)
            except Exception as e:
                yield self.create_text_message(
                    f"Error decoding file as UTF-8 text: {str(e)}"
                )
            return
        elif format == "file":
            yield self.create_blob_message(
                blob=file_bytes,
                meta={
                    "mime_type": data.get("mime_type"),
                    "filename": data.get("name"),
                },
            )
            return
