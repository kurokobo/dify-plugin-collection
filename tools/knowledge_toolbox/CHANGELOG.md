# Changelog

All notable changes to this project will be documented in this file.

## 0.0.5

- **Add File URL to Citations** and **Download File** tools now support Dify 1.13.1 or later by using the new `/datasets/{dataset_id}/documents/{document_id}/download` endpoint of the Knowledge API.
  - Dify 1.8.1 or earlier is still supported by falling back to the legacy `/upload-file` endpoint.
  - Dify 1.9.0 to 1.13.0 are not supported, and a clear error message is now returned instead.
- **Download File** tool now returns an error message for invalid Knowledge ID or Document ID.
- **Download File** tool now returns a hint for documents that cannot be downloaded, such as documents in Knowledge Pipelines on Dify 1.13.1 to 1.18.x.
- **Add File URL to Citations** tool now preserves the order of the referenced documents.
- `chunks_markdown` format of **Add File URL to Citations** tool now lists all chunks in a single collapsible `CITATIONS` block, each with the download link of the document, the chunk position, and the score.

## 0.0.4

- Added a warning to the documentation that **Add File URL to Citations** and **Download File** tools do not work with Dify versions newer than 1.8.1.

## 0.0.3

- Moved the API configurations (base URL and API key) to the plugin authorization configurations.

## 0.0.2

- Added a new tool: **Add File URL to Citations**.
- Added new output format `link` to the **Download File** tool, which provides a Markdown download link.

## 0.0.1

- Initial release of the Knowledge Toolbox plugin.
