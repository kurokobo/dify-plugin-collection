# 📦 Knowledge Toolbox - Small tools for working with Dify Knowledge API

- **Plugin ID** : kurokobo/knowledge_toolbox
- **Author** : kurokobo
- **Type** : tool
- **Repository** : https://github.com/kurokobo/dify-plugin-collection
- **Marketplace** : https://marketplace.dify.ai/plugins/kurokobo/knowledge_toolbox

## ✨ Overview

Small tools for working with Dify Knowledge API:

- ✅ **Add File URL to Citations**
  - Retrieves download URLs for files included in the results of the Knowledge Retrieval node and returns a list.
- ✅ **Download File**
  - Retrieve the uploaded file in Knowledge as a JSON, download URL, file object, or file content.
- ✅ **Get Full Doc**
  - Retrieve the full doc by concatenating all the chunks of the specified document in Knowledge.

## 🛠️ Bundled Tools

### ✅ Add File URL to Citations

This is a tool to retrieve the download URLs for files included in the results of the Knowledge Retrieval node.
With this tool, you can provide the download URLs of the files in the workflow results.

#### Parameters

- `api_base_url`
  - The base URL of the Knowledge API, with trailing `/v1`.
- `api_key`
  - The API key for the Knowledge API.
- `context`
  - The result of the Knowledge Retrieval node.
  - However, since Array[Object] cannot be selected directly here, please convert it to a string using a Template node or similar before inputting.
  - See the following section for details.
- `format`
  - The format of the output. See following section for details.

#### How to Input `context`

You can input the result of the Knowledge Retrieval node to the `context` parameter as follows:

- Connect new **Template** node to the Knowledge Retrieval node.
- Select `result` (`Array[Object]`) as the `arg1` of the **Template** node.
- Connect new **Add File URL to Citations** node to the **Template** node.
- Select `output` (`String`) of the **Template** node as the `context` of the **Add File URL to Citations** node.

#### Output Format

You can choose the output format:

- `full`
  - Returns a complete object with the metadata of the Knowledge Retrieval node results, adding a `download_url` field.
  - You can specify this as a context variable in the LLM node. For example, by using prompts such as, _"Please present the document you referred to with a download link using the URL in the `download_url` field"_, you can show users the actual document instead of just chunks.
  - However, due to technical limitations, if you specify this as a context variable in the LLM node, the chatbot's "Citations" feature will not work.
  - Additionally, depending on the accuracy of the LLM model, the URL may get rewritten during generation, resulting in invalid links.
- `minimal_json`
  - Returns a JSON string with basic information such as file names and download URLs of the referenced documents.
  - For instance, if you provide this JSON to the LLM along with the usual context and have it present download links when needed, you can generate download links while still utilizing the chatbot's Citations feature.
  - However, depending on the accuracy of the LLM model, the URL may get rewritten during generation, resulting in invalid links.
- `minimal_markdown`
  - Returns a list of Markdown formatted download links for the referenced documents.
  - By including this directly in the Answer node, you can completely prevent the issue of the URL being unintentionally altered by the LLM model and becoming unusable.
- `chunks_markdown`
  - Returns a collapsible Markdown that contains the referenced chunks and download links for the documents.
  - This can be used to replace the default Citations feature of the chatbot, by placing the output of this tool in the Answer node directly.

### ✅ Download File

This is a tool to retrieve the uploaded file in Knowledge.  
With this tool, you can use Knowledge like a simple file server. This is useful when you want to retrieve specific files or their contents within your workflow and use them as templates, for example.

If you want to retrieve the contents of a file that isn't plain text, the **✅ Get Full Doc** tool might be appropriate.

#### Parameters

- `api_base_url`
  - The base URL of the Knowledge API, with trailing `/v1`.
- `api_key`
  - The API key for the Knowledge API.
- `knowledge_id`
  - The ID of the Knowledge to retrieve the uploaded file from.
  - You can find this ID in the URL of each Knowledge page (`/datasets/<knowledge_id>`).
- `document_id`
  - The ID of the document that contains the uploaded file.
  - You can find this ID in the URL of each document page (`/datasets/<knowledge_id>/documents/<document_id>`).
- `format`
  - Format of the output. See following section for details.

#### Output Format

You can choose the output format of the file:

- `json`
  - As `text` output variable.
  - Raw response from the Knowledge API: `/datasets/{dataset_id}/documents/{document_id}/upload-file` (`GET`).
- `url`
  - As `text` output variable.
  - Download URL of the file.
- `file`
  - As `files` output variable.
  - File object of the file.
- `content`
  - As `text` output variable.
  - Content of the file as a string.

### ✅ Get Full Doc

This is a tool to retrieve the full doc by concatenating all the chunks of the specified document in Knowledge.
With this tool, for example, you can force the LLM node to always refer to the entire content of a specific document, which is quite useful.

#### Parameters

- `api_base_url`
  - The base URL of the Knowledge API, with trailing `/v1`.
- `api_key`
  - The API key for the Knowledge API.
- `knowledge_id`
  - The ID of the Knowledge to retrieve the uploaded file from.
  - You can find this ID in the URL of each Knowledge page (`/datasets/<knowledge_id>`).
- `document_id`
  - The ID of the document that contains the uploaded file.
  - You can find this ID in the URL of each document page (`/datasets/<knowledge_id>/documents/<document_id>`).
- `delimiter`
  - The string inserted between each chunk while joining them together.

#### Output Format

As `text` output variable, you can get the full doc of the specified document as a single (big, long) string by concatenating all of its chunks using the specified delimiter.

## 🕙 Changelog

See the [CHANGELOG.md](https://github.com/kurokobo/dify-plugin-collection/blob/main/tools/knowledge_toolbox/CHANGELOG.md) on GitHub for the latest updates and changes to this plugin.

## 📜 Privacy Policy

See the [PRIVACY.md](https://github.com/kurokobo/dify-plugin-collection/blob/main/tools/knowledge_toolbox/PRIVACY.md) on GitHub for details on how we handle user data and privacy.

## ℹ️ Contact Us

If you have any questions, suggestions, or issues regarding this plugin, please feel free to reach out to us through the following channels:

- [Open an issue on GitHub](https://github.com/kurokobo/dify-plugin-collection/issues)
- [Mention @kurokobo on GitHub](https://github.com/kurokobo)
- [Mention @kurokobo on the official Dify Discord serverl](https://discord.com/invite/FngNHpbcY7)

## 🔗 Related Links

- **Icon**: [Heroicons](https://heroicons.com/)
