"""
Transcription utilities for diarized speech-to-text
"""

from typing import Any
import io
import time

from yarl import URL
import openai

from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from dify_plugin.file.file import File

from tools.utils.audio_io import (
    AudioPayload,
    get_file_extension,
    is_audio_format,
    load_audio_from_bytes,
    split_audio_files,
    files_to_payloads,
)
from tools.utils.time_utils import adjust_segment_offsets
from tools.utils.segment_utils import update_segment_identifiers


def transcribe_diarized_chunk(
    client: openai.OpenAI | openai.AzureOpenAI,
    model: str,
    audio_bytes: bytes,
    extension: str,
    file_index: int,
    logger=None,
) -> tuple[list[dict[str, Any]], float]:
    audio_stream = io.BytesIO(audio_bytes)
    audio_stream.name = f"chunk.{extension}"

    if logger:
        logger.info("File %s: Transcribing chunk (%s)", file_index, extension)

    start_time = time.time()

    response = client.audio.transcriptions.create(
        file=audio_stream,
        model=model,
        response_format="diarized_json",
        timestamp_granularities=["segment"],
        chunking_strategy="auto",
    )

    api_duration = time.time() - start_time
    if logger:
        logger.info("File %s: API call finished in %.1fs", file_index, api_duration)

    if not response.segments:
        raise ToolProviderCredentialValidationError(
            f"File {file_index}: No segments returned from API (API call took {api_duration:.1f}s)"
        )

    segments = [seg.model_dump() for seg in response.segments]
    for seg in segments:
        seg.pop("type", None)
    audio_duration = None
    if extension:
        try:
            audio = load_audio_from_bytes(audio_bytes, extension)
            audio_duration = len(audio) / 1000.0
        except Exception:
            audio_duration = None
    if audio_duration is None:
        segment_ends = [seg.get("end") for seg in segments if isinstance(seg.get("end"), (int, float))]
        audio_duration = max(segment_ends) if segment_ends else 0.0
    if logger:
        logger.info("File %s: Received %s segment(s)", file_index, len(segments))
    return segments, audio_duration


def create_openai_client(
    service: str,
    api_key: str,
    base_url: str | None,
) -> openai.OpenAI | openai.AzureOpenAI:
    if service == "openai":
        return openai.OpenAI(api_key=api_key, base_url=str(URL(base_url) / "v1") if base_url else None)
    if service == "azure_openai":
        if not base_url:
            raise ToolProviderCredentialValidationError("API Base URL is required for Azure OpenAI")
        return openai.AzureOpenAI(api_key=api_key, api_version="2025-04-01-preview", azure_endpoint=base_url)
    raise ToolProviderCredentialValidationError(f"Unsupported service: {service}")


def _extract_text_response(response: Any) -> str:
    if isinstance(response, str):
        return response
    if hasattr(response, "text"):
        return str(response.text)
    return str(response)


def transcribe_text_files(
    client: openai.OpenAI | openai.AzureOpenAI,
    model: str,
    input_files: File | list[File] | AudioPayload | list[AudioPayload],
    logger,
) -> str:
    normalized_files = input_files if isinstance(input_files, list) else [input_files]
    texts: list[str] = []

    for file_index, input_file in enumerate(normalized_files, start=1):
        if not input_file:
            continue

        filename = getattr(input_file, "filename", None)
        extension = get_file_extension(filename) if filename else ""
        if not extension and hasattr(input_file, "extension"):
            extension = input_file.extension.lstrip(".")

        if not is_audio_format(extension):
            logger.info("File %s: Unsupported audio format (%s), skipping", file_index, extension)
            continue

        logger.info("File %s: %s format", file_index, extension.upper())

        audio_bytes = input_file.blob if hasattr(input_file, "blob") else input_file.data
        file_size_mb = len(audio_bytes) / (1024 * 1024)
        logger.info("File %s: %.1fMB", file_index, file_size_mb)

        audio_stream = io.BytesIO(audio_bytes)
        audio_stream.name = f"file_{file_index}.{extension}"

        response = client.audio.transcriptions.create(
            file=audio_stream,
            model=model,
            response_format="text",
        )
        text = _extract_text_response(response).strip()
        if text:
            texts.append(text)

    return "\n".join(texts).strip()


def diarize_audio_files(
    client: openai.OpenAI | openai.AzureOpenAI,
    model: str,
    input_files: File | AudioPayload | list[File] | list[AudioPayload],
    logger,
) -> tuple[list[dict[str, Any]], float]:
    normalized_files = input_files if isinstance(input_files, list) else [input_files]
    is_single_file = len(normalized_files) == 1

    all_segments: list[dict[str, Any]] = []
    offset_end = 0.0

    for file_index, input_file in enumerate(normalized_files, start=1):
        if not input_file:
            continue

        filename = getattr(input_file, "filename", None)
        extension = get_file_extension(filename) if filename else ""
        if not extension and hasattr(input_file, "extension"):
            extension = input_file.extension.lstrip(".")

        if not is_audio_format(extension):
            logger.info("File %s: Unsupported audio format (%s), skipping", file_index, extension)
            continue

        logger.info("File %s: %s format", file_index, extension.upper())

        audio_bytes = input_file.blob if hasattr(input_file, "blob") else input_file.data
        file_size_mb = len(audio_bytes) / (1024 * 1024)
        logger.info("File %s: %.1fMB", file_index, file_size_mb)

        segments, audio_duration = transcribe_diarized_chunk(
            client,
            model,
            audio_bytes,
            extension,
            file_index,
            logger,
        )
        if not is_single_file:
            update_segment_identifiers(segments, file_index, 0)
            adjust_segment_offsets(segments, offset_end)

        if not segments:
            continue

        all_segments.extend(segments)
        offset_end += float(audio_duration)
        logger.info(
            "File %s: Completed (%s segments, total offset: %.1fs)",
            file_index,
            len(segments),
            offset_end,
        )

    return all_segments, offset_end


def all_in_one_diarize_files(
    client: openai.OpenAI | openai.AzureOpenAI,
    model: str,
    input_files: File | list[File],
    auto_split: bool,
    use_silence_detection: bool,
    logger,
) -> tuple[list[dict[str, Any]], float]:
    if auto_split:
        payloads = split_audio_files(input_files, use_silence_detection=use_silence_detection, logger=logger)
    else:
        payloads = files_to_payloads(input_files, logger=logger)

    return diarize_audio_files(client, model, payloads, logger)


def all_in_one_transcribe_files(
    client: openai.OpenAI | openai.AzureOpenAI,
    model: str,
    input_files: File | list[File],
    auto_split: bool,
    use_silence_detection: bool,
    logger,
) -> str:
    if auto_split:
        payloads = split_audio_files(input_files, use_silence_detection=use_silence_detection, logger=logger)
    else:
        payloads = files_to_payloads(input_files, logger=logger)

    return transcribe_text_files(client, model, payloads, logger)
