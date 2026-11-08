# 📦 Knowledge Toolbox - Small tools for working with Dify Knowledge API

- **Plugin ID** : kurokobo/knowledge_toolbox
- **Author** : kurokobo
- **Type** : tool
- **Repository** : <https://github.com/kurokobo/dify-plugin-collection>
- **Marketplace** : <https://marketplace.dify.ai/plugins/kurokobo/knowledge_toolbox>

## ✨ Overview

Small tools for working with Dify Knowledge API:

- ✅ **Get Full Doc**
  - Retrieve the full doc by concatenating all the chunks of the specified document in Knowledge.
- ✅ **Add File URL to Citations**
  - Retrieves download URLs for files included in the results of the Knowledge Retrieval node and returns a list.
  - Requires Dify 1.13.1 or later (or 1.8.1 or earlier). See the **Supported Dify Versions** section below for details.
- ✅ **Download File**
  - Retrieve the uploaded file in Knowledge as a JSON, download URL, file object, or file content.
  - Requires Dify 1.13.1 or later (or 1.8.1 or earlier). See the **Supported Dify Versions** section below for details.

## ▶️ Demo App

The DSL file of the demo app for this plugin is available on GitHub.

- [💾 _examples/demo_knowledge_toolbox.yml](https://github.com/kurokobo/dify-plugin-collection/blob/main/tools/knowledge_toolbox/_examples/demo_knowledge_toolbox.yml).

## 📕 Setup Instructions

After installing the plugin, navigate to the `Tools` or `Plugins` page and then click on the **Knowledge Toolbox** plugin to configure it.  
By clicking on the `API Key Authorization Configuration` button, you can set following fields to use this plugin in your app.

- `Authorization Name`
  - The name of the authorization configuration, e.g. `Workspace A @ Dify Cloud`, `Workspace B @ Self-Hosted Dify`, etc.
- `Dify Knowledge API Base URL`
  - The base URL of the Dify Knowledge API, with trailing `/v1`.
  - For example, `https://api.dify.ai/v1` for Dify Cloud, or `http://api:5001/v1` for Docker-based self-hosted Dify.
- `Dify Knowledge API Key`
  - The API key for the Dify Knowledge API.
  - You can generate it at `Knowledge` > `API Access` > `API Key` in the Dify Console.

You can add multiple authorizations for different Dify Knowledge APIs, and can select one of them when using the tools in your app.

## ⚠️ Supported Dify Versions

**Get Full Doc** works with any Dify version.

**Add File URL to Citations** and **Download File** depend on the Knowledge API endpoint to get the download URL of the uploaded file, which differs by Dify version:

| Dify Version | Status | Endpoint |
| --- | --- | --- |
| 1.13.1 or later | ✅ Supported (Recommended) | `GET /datasets/{dataset_id}/documents/{document_id}/download` |
| 1.9.0 to 1.13.0 | ❌ Not supported | None ([removed](https://github.com/langgenius/dify/pull/25543)) |
| 1.8.1 or earlier | ✅ Supported (Legacy) | `GET /datasets/{dataset_id}/documents/{document_id}/upload-file` |

- The tools try the new endpoint first, and fall back to the legacy endpoint automatically.
- On unsupported versions, the tools return an error message as the `text` output instead of failing the node.
- Only documents created from files can be downloaded (not from Notion, websites, etc.).
- Documents in Knowledge Pipelines (`data_source_type` is `local_file`), including Knowledge converted to pipelines, can be downloaded only on Dify 1.19.0 or later. This is a limitation of the Knowledge API in Dify 1.13.1 to 1.18.x ([fixed in 1.19.0](https://github.com/langgenius/dify/pull/45428)), and the download link is not generated for such documents.

Note that the download URL is a signed URL issued by Dify:

- The URL expires after the time specified by `FILES_ACCESS_TIMEOUT` in Dify (`300` seconds by default). Links shown in a chat will no longer work after that.
- The host of the URL is determined by `FILES_URL` in Dify. To use the `file` or `content` format of **Download File**, the URL must be reachable from the plugin daemon.

## 🛠️ Bundled Tools

### ✅ Get Full Doc

This is a tool to retrieve the full doc by concatenating all the chunks of the specified document in Knowledge.
With this tool, for example, you can force the LLM node to always refer to the entire content of a specific document, which is quite useful.

#### Parameters

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

### ✅ Add File URL to Citations

> [!NOTE]
> This tool requires Dify 1.13.1 or later (or 1.8.1 or earlier). See the **Supported Dify Versions** section above for details.

This is a tool to retrieve the download URLs for files included in the results of the Knowledge Retrieval node.
With this tool, you can provide the download URLs of the files in the workflow results.

#### Parameters

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
  - Returns a collapsible Markdown that lists all referenced chunks in the order of the Knowledge Retrieval node results.
  - Each chunk is shown as a nested collapsible block (expanded by default) titled with the document name (clickable to download), the chunk position (`#<segment_position>`), and the score.
  - This can be used to replace the default Citations feature of the chatbot, by placing the output of this tool in the Answer node directly.

### ✅ Download File

> [!NOTE]
> This tool requires Dify 1.13.1 or later (or 1.8.1 or earlier). See the **Supported Dify Versions** section above for details.

This is a tool to retrieve the uploaded file in Knowledge.  
With this tool, you can use Knowledge like a simple file server. This is useful when you want to retrieve specific files or their contents within your workflow and use them as templates, for example.

If you want to retrieve the contents of a file that isn't plain text, the **✅ Get Full Doc** tool might be appropriate.

#### Parameters

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
  - File information as a JSON string, such as `name`, `size`, `extension`, `mime_type`, and `download_url`.
  - On Dify 1.8.1 or earlier, this is the raw response from the legacy `upload-file` endpoint.
  - On Dify 1.13.1 or later, some fields such as `id` and `size` are `null` for documents in Knowledge Pipelines (Dify 1.19.0 or later).
- `url`
  - As `text` output variable.
  - Download URL of the file.
- `link`
  - As `text` output variable.
  - Markdown download link of the file.
- `file`
  - As `files` output variable.
  - File object of the file.
- `content`
  - As `text` output variable.
  - Content of the file as a string.

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
