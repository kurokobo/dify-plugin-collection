from collections.abc import Generator
from typing import Any
import ast
import json

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.utils.knowledge_file_utils import (
    KnowledgeFileClient,
    KnowledgeFileError,
    UnsupportedDifyVersionError,
)
from tools.utils.logger_utils import get_logger

logger = get_logger(__name__)


class AddFileURLToCitationsTool(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        context = tool_parameters.get("context")
        format = tool_parameters.get("format", "full")

        if not self.runtime or not self.runtime.credentials:
            raise ToolProviderCredentialValidationError("Tool runtime or credentials are missing")

        api_base_url = self.runtime.credentials.get("api_base_url")
        api_key = self.runtime.credentials.get("api_key")

        if not api_base_url:
            raise ToolProviderCredentialValidationError("Knowledge API base URL is required.")
        if not api_key:
            raise ToolProviderCredentialValidationError("Knowledge API key is required.")

        # convert str to list of dictionaries
        try:
            context = ast.literal_eval(context)
        except Exception as e:
            yield self.create_text_message("Invalid context format. Please provide a valid context.")
            return

        # gather all documents in context (preserving order)
        documents = []
        document_names = {}
        for citation in context:
            metadata = citation.get("metadata") or {}
            key = (metadata.get("dataset_id"), metadata.get("document_id"))
            if key in document_names:
                continue
            document_names[key] = metadata.get("document_name") or ""
            documents.append({
                "dataset_id": key[0],
                "document_id": key[1],
            })

        # get the download url for each document
        client = KnowledgeFileClient(api_base_url, api_key)
        for document in documents:
            key = (document["dataset_id"], document["document_id"])
            try:
                data = client.get_file_info(
                    document["dataset_id"],
                    document["document_id"],
                    with_details=format == "minimal_json",
                )
            except UnsupportedDifyVersionError as e:
                yield self.create_text_message(f"Error fetching file information: {str(e)}")
                return
            except KnowledgeFileError as e:
                # e.g. documents not created from uploaded files, such as Notion or website
                logger.warning(f"Failed to get file information for document {key}: {str(e)}")
                data = {}

            document["download_url"] = data.get("download_url") or ""
            document['name'] = data.get("name") or document_names.get(key, "")
            document['size'] = data.get("size") or 0
            document['mime_type'] = data.get("mime_type") or ""

        # full: inject download urls into original context
        if format == "full":
            for citation in context:
                for document in documents:
                    if (citation.get("metadata").get("dataset_id") == document.get("dataset_id") and
                            citation.get("metadata").get("document_id") == document.get("document_id")):
                        citation["metadata"]["download_url"] = document.get(
                            "download_url")
            yield self.create_text_message(json.dumps(context, ensure_ascii=False))

        # minimal_json: return only referenced documents with download urls
        elif format == "minimal_json":
            yield self.create_text_message(json.dumps(documents, ensure_ascii=False))

        # minimal_markdown: return list of documents with download urls in markdown format
        elif format == "minimal_markdown":
            list = []
            for document in documents:
                list.append(
                    f"- [{document.get('name')}]({document.get('download_url')})")
            yield self.create_text_message("\n".join(list))

        # chunks_markdown: list all chunks as nested HTML details in the order of the context
        elif format == "chunks_markdown":
            from html import escape, unescape

            doc_dict = {
                (d.get("dataset_id"), d.get("document_id")): d for d in documents
            }

            chunk_blocks = []
            for citation in context:
                meta = citation.get("metadata") or {}
                doc_info = doc_dict.get((meta.get("dataset_id"), meta.get("document_id")), {})
                doc_name = escape(
                    meta.get("document_name") or doc_info.get("name") or citation.get("title") or ""
                )
                download_url = doc_info.get("download_url", "")

                # markdown links are not rendered inside <summary>, so use <a> tag instead
                summary = f'<a href="{escape(download_url)}">{doc_name}</a>' if download_url else doc_name
                position = meta.get("segment_position")
                if position is not None:
                    summary += f" #{position}"
                score = meta.get("score")
                if isinstance(score, (int, float)):
                    summary += f" ({score:.2f})"

                # escape "<" so that raw HTML tags in the chunk do not break the nested details
                content = unescape(citation.get("content") or "").replace("<", "&lt;")
                quoted = "\n".join(["> " + line for line in content.splitlines()]) or ">"
                chunk_blocks.append((summary, quoted))

            # put separators inside each details so that they are hidden when collapsed
            block = f"<details>\n<summary>CITATIONS ({len(chunk_blocks)})</summary>\n\n"
            for i, (summary, quoted) in enumerate(chunk_blocks):
                separator = "\n\n---" if i < len(chunk_blocks) - 1 else ""
                block += f"<details open>\n<summary>{summary}</summary>\n\n{quoted}{separator}\n\n</details>\n\n"
            block += "</details>"
            yield self.create_text_message(block)
