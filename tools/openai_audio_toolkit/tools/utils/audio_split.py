"""
Audio splitting utilities (silence-based and duration-based)
"""

from pydub import AudioSegment
from pydub.silence import detect_silence

DEFAULT_SILENCE_THRESH_DB = -40
DEFAULT_MIN_SILENCE_LEN_MS = 1000
DEFAULT_MIN_CHUNK_LEN_MS = 30000


def split_audio_on_silence(
    audio: AudioSegment,
    target_duration_ms: int,
    use_silence_detection: bool = True,
    silence_thresh: int = DEFAULT_SILENCE_THRESH_DB,
    min_silence_len: int = DEFAULT_MIN_SILENCE_LEN_MS,
    logger=None,
) -> list[AudioSegment]:
    """
    Split audio into chunks, attempting to cut at silence points if enabled.
    Ensures no chunk is smaller than DEFAULT_MIN_CHUNK_LEN_MS.
    """
    duration_ms = len(audio)

    if duration_ms <= target_duration_ms:
        if logger:
            logger.info(f"Audio duration {duration_ms}ms <= target {target_duration_ms}ms: no splitting needed")
        return [audio]

    if not use_silence_detection:
        if logger:
            logger.info(f"Silence detection disabled: using time-based splitting (target: {target_duration_ms}ms)")
        return split_audio_by_duration(audio, target_duration_ms)

    if logger:
        logger.info(
            f"Attempting silence-based splitting (silence_thresh: {silence_thresh}dB, min_len: {min_silence_len}ms)"
        )
    silence_ranges = detect_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
    )

    if logger:
        logger.info("Detected %s silence range(s)", len(silence_ranges))

    if not silence_ranges:
        if logger:
            logger.info(f"No silence detected: falling back to time-based splitting (target: {target_duration_ms}ms)")
        return split_audio_by_duration(audio, target_duration_ms)

    chunks = []
    start_ms = 0

    for silence_start, silence_end in silence_ranges:
        mid_silence = (silence_start + silence_end) // 2
        chunk_len = mid_silence - start_ms
        if chunk_len >= target_duration_ms and chunk_len >= DEFAULT_MIN_CHUNK_LEN_MS:
            if logger:
                logger.info(
                    "Splitting at %sms (chunk_len=%sms, target=%sms)",
                    mid_silence,
                    chunk_len,
                    target_duration_ms,
                )
            chunks.append(audio[start_ms:mid_silence])
            start_ms = mid_silence

    if start_ms < duration_ms:
        remaining = audio[start_ms:]
        if len(remaining) > target_duration_ms:
            if logger:
                logger.info(
                    "Remaining %sms exceeds target %sms: using time-based split",
                    len(remaining),
                    target_duration_ms,
                )
            chunks.extend(split_audio_by_duration(remaining, target_duration_ms))
        else:
            chunks.append(remaining)

    if len(chunks) == 0:
        if logger:
            logger.info(f"Silence-based splitting produced no chunks: falling back to time-based splitting")
        return split_audio_by_duration(audio, target_duration_ms)

    if logger:
        logger.info(f"Silence-based splitting successful: created {len(chunks)} chunks")
    return chunks


def split_audio_by_duration(audio: AudioSegment, max_duration_ms: int) -> list[AudioSegment]:
    """
    Split audio into fixed-duration chunks (fallback method).
    """
    chunks = []
    duration_ms = len(audio)
    for start_ms in range(0, duration_ms, max_duration_ms):
        end_ms = min(start_ms + max_duration_ms, duration_ms)
        chunks.append(audio[start_ms:end_ms])
    return chunks
