# 🎙️ OpenAI Audio Toolkit - Diarized Speech-to-Text Tools

- **Plugin ID** : kurokobo/openai_audio_toolkit
- **Author** : kurokobo
- **Type** : tool
- **Repository** : <https://github.com/kurokobo/dify-plugin-collection>
- **Marketplace** : <https://marketplace.dify.ai/plugins/kurokobo/openai_audio_toolkit>

## ✨ Overview

Tools for transcribing audio/video files using OpenAI or Azure OpenAI.

These tools are designed to provide a one-stop solution for transcribing even large files, including video files.
In addition to standard transcription, it also supports the use of speaker diarization models.
You can review the utterances for each speaker, replace the speaker names as needed, and output the results as text or files in various formats.

See the `▶️ Demo Apps (DSL)` section below for example apps using these tools.

There are two types of tools: **all-in-one tools** that auto-split and merge results, and **step-by-step tools** that run each stage separately.
Note that the all-in-one tools can be slow and may hit timeouts for large/long files; if that happens, use the step-by-step tools.

Self-hosted users: If you encounter file-size errors or node/app execution timeouts at runtime, consider tuning the environment variables in the **⚙️ Self-Hosted Tuning (Environment Variables)** section below.

- ✅ **All-in-One Diarize** (all-in-one)
  - Transcribes one or more audio/video files with speaker diarization enabled.
  - Outputs formatted text or files when `output_format` is specified.
  - Supports automatic splitting for large or long files (>25MB or >1500 seconds).
  - If inputs are split, each chunk is transcribed and the results are automatically merged with corrected time offsets and speaker IDs.

- ✅ **All-in-One Transcribe** (all-in-one)
  - Transcribes one or more audio/video files and outputs plain text only.
  - Supports automatic splitting for large or long files (>25MB or >1500 seconds).
  - If inputs are split, each chunk is transcribed and the results are automatically merged.

- ✅ **Split Audio** (step-by-step)
  - Splits audio files by size and duration limits.
  - API-native formats within limits are passed through; others are transcoded and/or split.
  - Optional silence detection for more natural splits.

- ✅ **Diarize Audio** (step-by-step)
  - Transcribes one or more audio files with speaker diarization enabled and outputs concatenated diarized segments as text and JSON.
  - Audio files are processed in the given order.

- ✅ **Transcribe Audio** (step-by-step)
  - Transcribes one or more audio files and outputs plain text only.
  - Audio files are processed in the given order.

- ✅ **Concat Segments** (step-by-step)
  - Concatenates multiple diarize-style outputs into a single segments array and outputs text and JSON.
  - Normalizes segment ids and offsets based on cumulative duration.

- ✅ **Review Speakers** (step-by-step)
  - Groups diarized segments by speaker to review utterances before `replace_speaker_name`, and outputs text, Markdown (list/collapsible), or JSON (text or file outputs).

- ✅ **Replace Speaker Name** (step-by-step)
  - Replaces auto-assigned sequential speaker names using user-provided rules and outputs JSON for downstream formatting.

- ✅ **Format Segments** (step-by-step)
  - Formats diarization segments into text, Markdown, VTT, or SRT (text or file outputs).

## ▶️ Demo Apps (DSL)

- [💾 **All-in-One Transcription**](https://raw.githubusercontent.com/kurokobo/dify-plugin-collection/refs/heads/main/tools/openai_audio_toolkit/examples/aio-transcription.yaml)
  - Transcribe one or more audio or video files using a standard transcription model.
  - Everything is handled in one tool: a simple app design. Depending on file input or Dify instance settings, a timeout may occur.

- [💾 **Step-by-Step Transcription**](https://raw.githubusercontent.com/kurokobo/dify-plugin-collection/refs/heads/main/tools/openai_audio_toolkit/examples/sbs-transcription.yaml)
  - Transcribe one or more audio or video files using a standard transcription model.
  - Each step for each file runs on a separate node: the chance of a timeout per node is low. However, hitting the overall app execution time limit is still possible.

- [💾 **All-in-One Diarization**](https://raw.githubusercontent.com/kurokobo/dify-plugin-collection/refs/heads/main/tools/openai_audio_toolkit/examples/aio-diarization.yaml)
  - Transcribe one or more audio or video files using a speaker diarization model.
  - Everything is handled in one tool: a simple app design. Depending on file input or Dify instance settings, a timeout may occur.

- [💾 **All-in-One Diarization with Adjusting Speaker Names**](https://raw.githubusercontent.com/kurokobo/dify-plugin-collection/refs/heads/main/tools/openai_audio_toolkit/examples/aio-diarization-speaker-names.yaml)
  - Transcribe one or more audio or video files using a speaker diarization model.
  - In a chatbot format, you can interactively review and edit speaker names.

- [💾 **Step-by-Step Diarization**](https://raw.githubusercontent.com/kurokobo/dify-plugin-collection/refs/heads/main/tools/openai_audio_toolkit/examples/sbs-diarization.yaml)
  - Transcribe one or more audio or video files using a speaker diarization model.
  - Each step for each file runs on a separate node: the chance of a timeout per node is low. However, hitting the overall app execution time limit is still possible.

- [💾 **Step-by-Step Diarization with Adjusting Speaker Names**](https://raw.githubusercontent.com/kurokobo/dify-plugin-collection/refs/heads/main/tools/openai_audio_toolkit/examples/sbs-diarization-speaker-names.yaml)
  - Transcribe one or more audio or video files using a speaker diarization model.
  - In a chatbot format, you can interactively review and edit speaker names.

## 📕 Setup Instructions

After installing the plugin, navigate to the `Tools` or `Plugins` page and then click on the **OpenAI Audio Toolkit** plugin to configure it.
By clicking on the `API Key Authorization Configuration` button, you can set following fields to use this plugin in your app.

- `Service`
  - Choose between `OpenAI` or `Azure OpenAI`.
- `API Key`
  - The API key for the selected service.
  - For OpenAI: Your API key from <https://platform.openai.com/account/api-keys>.
  - For Azure OpenAI: Your API key from the Azure portal.
- `API Base URL` (Optional for OpenAI, Required for Azure OpenAI)
  - For OpenAI: Leave empty or provide a custom base URL.
  - For Azure OpenAI: The base URL of your resource (e.g., `https://your-resource.openai.azure.com`).
- `Model name or deployment name`
  - A speech-to-text model (diarization-capable for diarize tools).
  - For OpenAI: Use `gpt-4o-transcribe-diarize` for diarization.
  - For Azure OpenAI: Use your deployment name which is based on `gpt-4o-transcribe-diarize`.
  - If you are not using diarization tools, a regular speech-to-text model is fine.

You can add multiple authorizations for different services or accounts, and can select one of them when using the tools in your app.

## ⚙️ Self-Hosted Tuning (Environment Variables)

If you run a self-hosted Dify instance and see file-size related errors, or node/app execution timeouts, review and tune the following environment variables.
Edit your `.env` file and restart the instance with `docker compose down` and `docker compose up -d` to apply changes.

### File size related

- `UPLOAD_VIDEO_FILE_SIZE_LIMIT`
- `UPLOAD_AUDIO_FILE_SIZE_LIMIT`
- `NGINX_CLIENT_MAX_BODY_SIZE`

### Timeout related

- `APP_MAX_EXECUTION_TIME`
- `WORKFLOW_MAX_EXECUTION_TIME`
- `PLUGIN_MAX_EXECUTION_TIMEOUT`
- `PLUGIN_DAEMON_TIMEOUT`

## 🛠️ Bundled Tools

### ✅ All-in-One Diarize

Transcribes one or more audio/video files with speaker diarization enabled and outputs formatted text or files when `output_format` is specified.
Supports automatic splitting for large or long files (>25MB or >1500 seconds).
If inputs are split, each chunk is transcribed and the results are automatically merged with corrected time offsets and speaker IDs.

⚠️ **Performance Notice** ⚠️

- **Speaker diarization transcription is inherently slow. Additionally, this tool handles all processing steps in a single operation.**
- **For large or long files, this may result in timeout errors unless you have a well-tuned self-hosted environment.**
- **In such cases, consider using the step-by-step individual tools below to execute each processing step separately within your workflow.**

#### Parameters

- `input_files`
  - One or more audio/video files to transcribe with speaker diarization enabled.
  - Supported audio formats: MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM
  - Supported video formats: MP4, MPEG, MPG, WEBM, AVI, MOV, FLV, MKV
  - Files are processed in the order specified and results are concatenated.

- `auto_split` (Optional, default: enabled)
  - Automatically split files larger than 25MB or longer than 1500 seconds into smaller chunks to avoid API limits.
  - If disabled, files are sent as-is and must already be accepted by the API (e.g., `split_audio` outputs).

- `use_silence_detection` (Optional, default: disabled)
  - When auto-split is enabled, split audio at detected silence points instead of fixed time intervals.
  - This produces more natural splits but may be slower.
  - Falls back to time-based splitting if no silence is detected.

#### Output Format

- If `output_format` is set, returns formatted text or a formatted file.
- Supported formats: `plain_text`, `markdown_text`, `vtt_text`, `srt_text`, `json_text` and their `*_file` variants.

### ✅ All-in-One Transcribe

Transcribes one or more audio/video files and outputs plain text only.
Supports automatic splitting for large or long files (>25MB or >1500 seconds).
If inputs are split, each chunk is transcribed and the results are automatically merged.

#### Parameters

- `input_files`
  - One or more audio/video files to transcribe.
  - Various audio/video formats are supported.
  - Files are processed in the order specified.

- `auto_split` (Optional, default: enabled)
  - Automatically split files larger than 25MB or longer than 1500 seconds into smaller chunks to avoid API limits.

- `use_silence_detection` (Optional, default: disabled)
  - When auto-split is enabled, split audio at detected silence points instead of fixed time intervals.
  - Falls back to time-based splitting if no silence is detected.

- `output_format` (Optional, default: plain_text)
  - `plain_text` or `plain_file`.

#### Output Format

Returns a text message or a text file containing the concatenated transcript.

### ✅ Split Audio

Splits audio/video files based on file size and duration limits. MP4 files with supported audio codecs may be extracted as audio.

#### Parameters

- `input_files`
  - One or more audio/video files to split if necessary.

- `use_silence_detection` (Optional, default: disabled)
  - Split at silence points when splitting is needed; falls back to time-based splitting.
  - Enabling this produces more natural splits but may be slower.

#### Output Format

Returns one or more audio files (blobs). Files in API-native formats within limits pass through; others are transcoded and/or split.

### ✅ Diarize Audio

Transcribes one or more audio files with speaker diarization enabled and outputs concatenated diarized segments as text and JSON.
Usually, use the outputs of `split_audio` as inputs.

#### Parameters

- `input_files`
  - One or more audio files to transcribe with speaker diarization enabled.
  - Supported audio formats: MP3, WAV, AAC, FLAC, OGG, M4A, WMA, OPUS
  - Inputs must already be accepted by the API (e.g., `split_audio` outputs).
  - Files are processed in the order specified and results are concatenated.

#### Output Format

Returns text and JSON messages containing:

- `segments`: Array of diarized segments exactly as provided by the API, with the following structure:
  - `id`: Unique segment identifier
  - `start`: Segment start time in seconds
  - `end`: Segment end time in seconds
  - `text`: Transcribed text
  - `speaker`: Speaker identifier
- `metadata`: Overall processing metadata
  - `total_duration_sec`: Total duration in seconds across processed files

When processing multiple files:

- Speaker IDs are prefixed with file indices (e.g., `1-A`, `2-B`)
- Segment IDs include file context (e.g., `file_1/seg_0`, `file_2/seg_0`)
- Time offsets are adjusted to reflect the cumulative position across all files

### ✅ Transcribe Audio

Transcribes one or more audio files and outputs plain text only.
Usually, use the outputs of `split_audio` as inputs.

#### Parameters

- `input_files`
  - One or more audio files to transcribe.
  - Supported audio formats: MP3, WAV, AAC, FLAC, OGG, M4A, WMA, OPUS
  - Inputs must already be accepted by the API (e.g., `split_audio` outputs).
  - Files are processed in the order specified.

#### Output Format

Returns a text message containing the concatenated transcript.

### ✅ Concat Segments

Concatenates an array of diarize-like outputs and normalizes segment ids and time offsets.
Usually, use the outputs of multiple `diarize_audio` calls as inputs.

#### Parameters

- `items_json_string`
  - JSON string of an array of objects with `segments` and optional `metadata`.
  - Each element should match the `diarize_audio` output shape.

- `items_array` (experimental)
  - Array of objects with `segments` and optional `metadata`.

#### Output Format

Returns text and JSON messages containing:

- `segments`: Concatenated segments with updated `id`, `start`, and `end`
- `metadata`:
  - `total_duration_sec`: Total duration across all items
  - `item_count`: Number of items in input
  - `segment_count`: Total number of segments

### ✅ Review Speakers

To review speaker-wise utterances before replacing auto-assigned sequential speaker names with the `replace_speaker_name` tool, groups diarized segments by speaker and outputs text, Markdown (list/collapsible), or JSON.
Usually, use the output of `diarize_audio`, `concat_segments`, or `format_segments` as input.

#### Parameters

- `segments_json_string`
  - JSON string of a diarize-style object or array (e.g., `diarize_audio` / `concat_segments` / `format_segments` JSON output).

- `segments_json_file`
  - JSON file that contains a diarize-style segments payload (e.g., `format_segments` JSON file output).

- `output_format`
  - `plain_text`, `plain_file`, `markdown_list_text`, `markdown_list_file`,
    `markdown_collapsible_text`, `markdown_collapsible_file`, `json_text`, or `json_file`.

- `preview_limit`
  - Maximum number of transcript items per speaker. Use `0` for unlimited.

### ✅ Replace Speaker Name

Replaces auto-assigned sequential speaker names using user-provided rules and outputs text and JSON for downstream formatting.
Usually, use the output of `diarize_audio`, `concat_segments`, or `format_segments` as input.

#### Parameters

- `segments_json_string`
  - JSON string of a diarize-style object or array (e.g., `diarize_audio` / `concat_segments` / `format_segments` JSON output).

- `segments_json_file`
  - JSON file that contains a diarize-style segments payload (e.g., `format_segments` JSON file output).

- `replace_rules`
  - One rule per line in `from:to` format (colon is not allowed in names).
  - Example:
    - `Speaker1:John Doe`
    - `1-A:Alice`

#### Output Format

Returns text and JSON messages containing the replaced segments.

### ✅ Format Segments

Formats diarization segments into text, Markdown, VTT, or SRT.
Usually, use the output of `diarize_audio`, `concat_segments`, or `replace_speaker_name` as input.

#### Parameters

- `segments_json_string`
  - JSON string of a diarize-style object (e.g., `diarize_audio` / `concat_segments` / `replace_speaker_name` text output).

- `output_format`
  - `plain_text`, `markdown_text`, `vtt_text`, `srt_text`, `json_text` or their `*_file` variants.

## 📜 Privacy Policy

See [PRIVACY.md](./PRIVACY.md) for details on data handling.

## ℹ️ Contact Us

If you have any questions, suggestions, or issues regarding this plugin, please feel free to reach out to us through the following channels:

- [Open an issue on GitHub](https://github.com/kurokobo/dify-plugin-collection/issues)
- [Mention @kurokobo on GitHub](https://github.com/kurokobo)
- [Mention @kurokobo on the official Dify Discord server](https://discord.com/invite/FngNHpbcY7)

## 🔗 Related Links

- **Icon**: [Heroicons](https://heroicons.com/)
- **OpenAI API for Speech to text**: <https://platform.openai.com/docs/guides/speech-to-text>
