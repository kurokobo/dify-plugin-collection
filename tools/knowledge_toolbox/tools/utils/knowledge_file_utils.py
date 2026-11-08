import mimetypes
import os
import uuid
from typing import Any

import requests

# Body of the 404 response returned by Flask/Werkzeug when no route matches the request
ROUTE_NOT_FOUND_MARKER = "requested url was not found"

UNSUPPORTED_VERSION_MESSAGE = (
    "The Knowledge API of this Dify instance does not provide any endpoint to download files. "
    "This tool requires Dify 1.13.1 or later (recommended), or Dify 1.8.1 or earlier. "
    "Dify 1.9.0 to 1.13.0 are not supported."
)

# Message returned by Dify when the document is not backed by a downloadable file
NO_UPLOADED_FILE_MARKER = "does not have an uploaded file"

NO_UPLOADED_FILE_HINT = (
    "Only documents created from files can be downloaded. "
    "Documents in Knowledge Pipelines (including Knowledge converted to pipelines) "
    "can be downloaded only on Dify 1.19.0 or later."
)


class KnowledgeFileError(Exception):
    """Raised when the file information of a document cannot be retrieved."""


class UnsupportedDifyVersionError(KnowledgeFileError):
    """Raised when the Knowledge API provides no endpoint to download files."""


class KnowledgeFileClient:
    """
    Resolve download URLs of files uploaded to Dify Knowledge.

    - Dify 1.13.1 or later: GET /datasets/{dataset_id}/documents/{document_id}/download
      (file details are retrieved from GET /datasets/{dataset_id}/documents/{document_id})
    - Dify 1.8.1 or earlier: GET /datasets/{dataset_id}/documents/{document_id}/upload-file
    - Dify 1.9.0 to 1.13.0: no endpoint is available
    """

    def __init__(self, api_base_url: str, api_key: str):
        self.api_base_url = api_base_url.rstrip("/")
        self.headers = {
            "authorization": f"bearer {api_key}",
            "content-type": "application/json",
        }
        # "download", "legacy", or None (not detected yet)
        self.api_mode: str | None = None

    def get_file_info(self, dataset_id: str, document_id: str, with_details: bool = True) -> dict[str, Any]:
        """
        Return the information of the file uploaded as the document, including "download_url".

        If with_details is False, file details such as "name", "size", and "mime_type" may be
        missing, which saves an extra API request on Dify 1.13.1 or later.
        """
        self._validate_id(dataset_id, "Knowledge ID")
        self._validate_id(document_id, "Document ID")

        if self.api_mode != "legacy":
            info = self._get_file_info_via_download(dataset_id, document_id, with_details)
            if info is not None:
                self.api_mode = "download"
                return info

        if self.api_mode != "download":
            info = self._get_file_info_via_upload_file(dataset_id, document_id)
            if info is not None:
                self.api_mode = "legacy"
                return info

        raise UnsupportedDifyVersionError(UNSUPPORTED_VERSION_MESSAGE)

    def _get_file_info_via_download(
        self, dataset_id: str, document_id: str, with_details: bool
    ) -> dict[str, Any] | None:
        response = self._get(f"/datasets/{dataset_id}/documents/{document_id}/download")
        if self._is_route_not_found(response):
            return None
        if response.status_code == 404 and NO_UPLOADED_FILE_MARKER in response.text.lower():
            raise KnowledgeFileError(
                f"Fetching the download URL failed with HTTP 404: {self._error_message(response)} "
                f"{NO_UPLOADED_FILE_HINT}"
            )
        self._raise_for_status(response, "Fetching the download URL")

        download_url = self._json(response).get("url")
        if not download_url:
            raise KnowledgeFileError("No download URL found in the response.")

        info: dict[str, Any] = {
            "id": None,
            "name": None,
            "size": None,
            "extension": None,
            "mime_type": None,
            "created_by": None,
            "created_at": None,
            "download_url": download_url,
        }
        if with_details:
            info.update(self._get_file_details(dataset_id, document_id))
        return info

    def _get_file_details(self, dataset_id: str, document_id: str) -> dict[str, Any]:
        response = self._get(
            f"/datasets/{dataset_id}/documents/{document_id}",
            params={"metadata": "without"},
        )
        self._raise_for_status(response, "Fetching the document details")

        document = self._json(response)
        data_source_info = document.get("data_source_info")
        upload_file = data_source_info.get("upload_file") if isinstance(data_source_info, dict) else None
        if not isinstance(upload_file, dict):
            # Documents created via RAG pipelines have no upload_file details
            upload_file = {}

        name = upload_file.get("name") or document.get("name") or ""
        extension = upload_file.get("extension") or os.path.splitext(name)[1].lstrip(".")
        mime_type = (
            upload_file.get("mime_type")
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream"
        )
        return {
            "id": upload_file.get("id"),
            "name": name,
            "size": upload_file.get("size"),
            "extension": extension,
            "mime_type": mime_type,
            "created_by": upload_file.get("created_by"),
            "created_at": upload_file.get("created_at"),
        }

    def _get_file_info_via_upload_file(self, dataset_id: str, document_id: str) -> dict[str, Any] | None:
        response = self._get(f"/datasets/{dataset_id}/documents/{document_id}/upload-file")
        if self._is_route_not_found(response):
            return None
        self._raise_for_status(response, "Fetching the upload-file endpoint")

        data = self._json(response)
        if not data.get("download_url"):
            raise KnowledgeFileError("No download URL found in the response.")
        return data

    def _get(self, path: str, params: dict[str, Any] | None = None) -> requests.Response:
        try:
            return requests.get(f"{self.api_base_url}{path}", headers=self.headers, params=params)
        except Exception as e:
            raise KnowledgeFileError(f"Failed to connect to the Knowledge API: {str(e)}") from e

    @staticmethod
    def _validate_id(value: str, label: str) -> None:
        # Invalid IDs never match any route and would be mistaken for an unsupported version
        try:
            uuid.UUID(str(value))
        except (ValueError, TypeError):
            raise KnowledgeFileError(f"Invalid {label}: {value!r}. It must be a UUID.")

    @staticmethod
    def _is_route_not_found(response: requests.Response) -> bool:
        return response.status_code == 404 and ROUTE_NOT_FOUND_MARKER in response.text.lower()

    @staticmethod
    def _json(response: requests.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except Exception as e:
            raise KnowledgeFileError(f"Invalid response from the Knowledge API: {str(e)}") from e
        if not isinstance(data, dict):
            raise KnowledgeFileError("Invalid response from the Knowledge API: JSON object expected.")
        return data

    @staticmethod
    def _error_message(response: requests.Response) -> str:
        message = response.text.strip()
        try:
            data = response.json()
            if isinstance(data, dict) and data.get("message"):
                message = str(data.get("message"))
        except Exception:
            pass
        return message[:500]

    @classmethod
    def _raise_for_status(cls, response: requests.Response, action: str) -> None:
        if response.ok:
            return
        raise KnowledgeFileError(
            f"{action} failed with HTTP {response.status_code}: {cls._error_message(response)}"
        )
