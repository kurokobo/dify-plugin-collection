"""
Audio I/O utilities (load, export, compress, demux, format detection)
"""

import io
import json
import mimetypes
import subprocess
import tempfile
from dataclasses import dataclass
from dify_plugin.file.file import File

from pydub import AudioSegment

from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from tools.utils.audio_split import split_audio_on_silence


@dataclass(frozen=True)
class AudioPayload:
    filename: str
    data: bytes
    mime_type: str


# API limits
MAX_FILE_SIZE_MB = 25  # API limit on maximum file size
MAX_DURATION_SEC = 1500  # API limit on maximum audio duration
API_LIMIT_SAFETY_MARGIN = 0.95  # Safety margin to avoid hitting exact API limits
BITRATE_BYTES_PER_SEC = 64 * 1024 / 8  # 64kbps = 8192 bytes/sec
MODEL_NATIVE_AUDIO_FORMATS = {
    "mp3",
    "mp4",
    "mpeg",
    "mpga",
    "m4a",
    "wav",
    "webm",
}
SUPPORTED_MP4_AUDIO_CODECS = {
    "aac",
    "mp3",
}


def calculate_target_duration_ms() -> int:
    """
    Calculate target duration in milliseconds based on API limits and bitrate.
    Respects both file size limit (25MB) and duration limit (1500s).

    Returns:
        Target duration in milliseconds (respects API limits)
    """
    # Calculate duration based on file size and bitrate
    target_duration_sec = (MAX_FILE_SIZE_MB * 1024 * 1024) / BITRATE_BYTES_PER_SEC
    target_duration_sec = target_duration_sec * API_LIMIT_SAFETY_MARGIN

    # Respect the API limit for duration with safety margin applied
    max_duration_sec = MAX_DURATION_SEC * API_LIMIT_SAFETY_MARGIN
    target_duration_sec = min(target_duration_sec, max_duration_sec)

    return int(target_duration_sec * 1000)


def should_split_audio(file_size_mb: float, duration_sec: float) -> bool:
    """
    Determine if audio file should be split based on size and duration limits.

    Args:
        file_size_mb: File size in megabytes
        duration_sec: Audio duration in seconds

    Returns:
        True if file should be split, False otherwise
    """
    size_threshold_mb = MAX_FILE_SIZE_MB * API_LIMIT_SAFETY_MARGIN
    duration_threshold_sec = MAX_DURATION_SEC * API_LIMIT_SAFETY_MARGIN
    return file_size_mb > size_threshold_mb or duration_sec > duration_threshold_sec


def is_duration_exceeding_limit(duration_sec: float) -> bool:
    duration_threshold_sec = MAX_DURATION_SEC * API_LIMIT_SAFETY_MARGIN
    return duration_sec > duration_threshold_sec


def estimate_compressed_size_mb(duration_sec: float) -> float:
    return (duration_sec * BITRATE_BYTES_PER_SEC) / (1024 * 1024)


def get_file_extension(filename: str) -> str:
    if "." in filename:
        return filename.rsplit(".", 1)[-1]
    return ""


def get_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def is_audio_format(extension: str) -> bool:
    audio_formats = {
        "mp3",
        "wav",
        "aac",
        "flac",
        "ogg",
        "m4a",
        "wma",
        "opus",
        "mp4",
        "mpeg",
        "mpga",
        "mpg",
        "webm",
        "avi",
        "mov",
        "flv",
        "mkv",
    }
    return extension.lower() in audio_formats


def calculate_file_size_mb(data: bytes) -> float:
    return len(data) / (1024 * 1024)


def _build_payload(filename: str, data: bytes) -> AudioPayload:
    return AudioPayload(
        filename=filename,
        data=data,
        mime_type=get_mime_type(filename),
    )


def load_audio_from_bytes(audio_bytes: bytes, extension: str) -> AudioSegment:
    try:
        return AudioSegment.from_file(io.BytesIO(audio_bytes), format=extension)
    except Exception as exc:
        raise ToolProviderCredentialValidationError(f"Failed to load audio/video file: {str(exc)}")


def export_compressed_audio(audio: AudioSegment, format: str = "ipod", codec: str = "aac", parameters=None) -> bytes:
    if parameters is None:
        parameters = ["-ac", "1", "-ar", "16000", "-b:a", "64k"]
    buffer = io.BytesIO()
    audio.export(buffer, format=format, codec=codec, parameters=parameters)
    return buffer.getvalue()


def is_native_audio_format(extension: str) -> bool:
    return extension.lower() in MODEL_NATIVE_AUDIO_FORMATS


def is_within_size_limit(file_size_mb: float) -> bool:
    size_threshold_mb = MAX_FILE_SIZE_MB * API_LIMIT_SAFETY_MARGIN
    return file_size_mb <= size_threshold_mb


def probe_mp4_streams(data: bytes, logger=None) -> tuple[bool, float | None, bool, str | None]:
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp_file:
            tmp_file.write(data)
            tmp_file.flush()
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_streams",
                    "-of",
                    "json",
                    tmp_file.name,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        if result.returncode != 0:
            if logger:
                logger.info("FFprobe failed: %s", (result.stderr or result.stdout).strip())
            return False, None, False, None

        payload = json.loads(result.stdout)
        streams = payload.get("streams", [])
        audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
        video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]

        duration_sec = None
        for stream in audio_streams:
            if stream.get("duration"):
                try:
                    duration_sec = float(stream["duration"])
                    break
                except (ValueError, TypeError):
                    duration_sec = None
        if duration_sec is None:
            format_info = payload.get("format", {})
            if format_info.get("duration"):
                try:
                    duration_sec = float(format_info["duration"])
                except (ValueError, TypeError):
                    duration_sec = None

        has_video = len(video_streams) > 0
        if len(audio_streams) != 1:
            return False, duration_sec, has_video, None

        codec_name = str(audio_streams[0].get("codec_name", "")).lower()
        return codec_name in SUPPORTED_MP4_AUDIO_CODECS, duration_sec, has_video, codec_name or None
    except Exception as exc:
        if logger:
            logger.info("FFprobe error: %s", exc)
        return False, None, False, None


def _get_audio_extension_for_codec(codec_name: str | None) -> str | None:
    if codec_name == "aac":
        return "m4a"
    if codec_name == "mp3":
        return "mp3"
    return None


def extract_audio_from_mp4_copy(data: bytes, output_extension: str, logger=None) -> bytes:
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp_input, tempfile.NamedTemporaryFile(
            suffix=f".{output_extension}"
        ) as tmp_output:
            tmp_input.write(data)
            tmp_input.flush()

            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    tmp_input.name,
                    "-vn",
                    "-acodec",
                    "copy",
                    "-map",
                    "0:a:0",
                    tmp_output.name,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                if logger:
                    logger.info("FFmpeg extract failed: %s", (result.stderr or result.stdout).strip())
                raise ToolProviderCredentialValidationError("Failed to extract audio stream from MP4")

            tmp_output.seek(0)
            return tmp_output.read()
    except ToolProviderCredentialValidationError:
        raise
    except Exception as exc:
        if logger:
            logger.info("FFmpeg extract error: %s", exc)
        raise ToolProviderCredentialValidationError("Failed to extract audio stream from MP4")


def split_audio_file(
    audio: AudioSegment,
    filename: str,
    use_silence_detection: bool,
    logger,
) -> list[AudioPayload]:
    original_duration_sec = audio.duration_seconds
    estimated_size_mb = estimate_compressed_size_mb(original_duration_sec)
    if logger:
        logger.info(
            "Estimated compressed size: %.1fMB, duration: %.1fs",
            estimated_size_mb,
            original_duration_sec,
        )

    needs_splitting = should_split_audio(estimated_size_mb, original_duration_sec)
    if not needs_splitting:
        if logger:
            logger.info("No splitting needed; compressing")
        compressed_audio = export_compressed_audio(audio)
        base_filename = filename.rsplit(".", 1)[0]
        compressed_filename = f"{base_filename}.m4a"
        return [
            _build_payload(
                compressed_filename,
                compressed_audio,
            )
        ]

    if logger:
        logger.info("Splitting audio (silence detection: %s)", "enabled" if use_silence_detection else "disabled")
    target_duration_ms = calculate_target_duration_ms()
    audio_chunks = split_audio_on_silence(
        audio,
        target_duration_ms,
        use_silence_detection=use_silence_detection,
        logger=logger,
    )
    if logger:
        logger.info("Created %s chunk(s)", len(audio_chunks))

    result: list[AudioPayload] = []
    base_filename = filename.rsplit(".", 1)[0]
    for chunk_idx, chunk in enumerate(audio_chunks, 1):
        logger.info("Compressing chunk %s/%s", chunk_idx, len(audio_chunks))
        compressed_chunk = export_compressed_audio(chunk)
        chunk_filename = f"{base_filename}_chunk{chunk_idx:03d}.m4a"
        result.append(_build_payload(chunk_filename, compressed_chunk))

    return result


def _split_audio_items(
    items: list[tuple[str, bytes]],
    use_silence_detection: bool,
    logger=None,
    item_label: str = "Item",
) -> list[AudioPayload]:
    output_files: list[AudioPayload] = []
    for item_index, (filename, data) in enumerate(items, start=1):
        if logger:
            logger.info("%s %s: processing", item_label, item_index)

        extension = get_file_extension(filename)
        if not is_audio_format(extension):
            if logger:
                logger.info("%s %s: unsupported audio format, skipped", item_label, item_index)
            continue

        file_size_mb = calculate_file_size_mb(data)
        if extension.lower() == "mp4":
            is_audio_only_supported, duration_sec, has_video, codec_name = probe_mp4_streams(data, logger=logger)
            if duration_sec is not None and is_duration_exceeding_limit(duration_sec):
                if logger:
                    logger.info("%s %s: duration exceeds limit; splitting", item_label, item_index)
                audio = load_audio_from_bytes(data, extension)
                output_files.extend(split_audio_file(audio, filename, use_silence_detection, logger))
                continue
            if (
                duration_sec is not None
                and is_audio_only_supported
                and is_native_audio_format(extension)
                and is_within_size_limit(file_size_mb)
            ):
                if logger:
                    logger.info("%s %s: mp4 audio-only pass-through", item_label, item_index)
                output_files.append(_build_payload(filename, data))
                continue
            if has_video and duration_sec is not None and codec_name in SUPPORTED_MP4_AUDIO_CODECS:
                output_extension = _get_audio_extension_for_codec(codec_name)
                if output_extension:
                    if logger:
                        logger.info("%s %s: extracting audio stream (copy)", item_label, item_index)
                    extracted = extract_audio_from_mp4_copy(data, output_extension, logger=logger)
                    extracted_size_mb = calculate_file_size_mb(extracted)
                    if is_within_size_limit(extracted_size_mb) and is_native_audio_format(output_extension):
                        base_filename = filename.rsplit(".", 1)[0]
                        output_filename = f"{base_filename}.{output_extension}"
                        output_files.append(_build_payload(output_filename, extracted))
                        continue

        audio = load_audio_from_bytes(data, extension)
        if is_duration_exceeding_limit(audio.duration_seconds):
            if logger:
                logger.info("%s %s: duration exceeds limit; splitting", item_label, item_index)
            output_files.extend(split_audio_file(audio, filename, use_silence_detection, logger))
            continue

        if is_native_audio_format(extension) and is_within_size_limit(file_size_mb):
            if logger:
                logger.info("%s %s: native format pass-through", item_label, item_index)
            output_files.append(_build_payload(filename, data))
            continue

        output_files.extend(split_audio_file(audio, filename, use_silence_detection, logger))

    return output_files


def split_audio_files(
    input_files: File | list[File],
    use_silence_detection: bool = False,
    logger=None,
) -> list[AudioPayload]:
    normalized_files = input_files if isinstance(input_files, list) else [input_files]
    items = [(file_item.filename, file_item.blob) for file_item in normalized_files]
    return _split_audio_items(items, use_silence_detection, logger=logger, item_label="File")


def files_to_payloads(
    input_files: File | list[File],
    logger=None,
) -> list[AudioPayload]:
    normalized_files = input_files if isinstance(input_files, list) else [input_files]
    payloads: list[AudioPayload] = []
    for file_index, file_item in enumerate(normalized_files, start=1):
        if logger:
            logger.info("File %s: processing", file_index)
        filename = file_item.filename
        extension = get_file_extension(filename)
        if not is_audio_format(extension):
            if logger:
                logger.info("File %s: unsupported format, skipped", file_index)
            continue
        payloads.append(_build_payload(filename, file_item.blob))
    return payloads
