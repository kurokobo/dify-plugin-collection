from collections.abc import Generator
from typing import Any
from pydub import AudioSegment
import math
import io

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class SimpleBGMMixerTool(Tool):
    @staticmethod
    def _extract_values(colon_separated_string: str) -> list[float]:
        return [float(value) for value in colon_separated_string.split(":") if value.strip()]

    @staticmethod
    def _convert_ratio_to_db(ratio):
        return 20 * math.log10(ratio)

    @staticmethod
    def _get_mime_type(output_format: str) -> str:
        mime_types = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
        }
        return mime_types.get(output_format, "audio/mpeg")

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        try:
            # params
            audio_file_1 = tool_parameters.get("audio_file_1")
            audio_file_2 = tool_parameters.get("audio_file_2")
            audio_file_3 = tool_parameters.get("audio_file_3")
            audio_file_4 = tool_parameters.get("audio_file_4")
            audio_file_5 = tool_parameters.get("audio_file_5")
            audio_files = [
                audio_file for audio_file in [
                    audio_file_1, audio_file_2, audio_file_3, audio_file_4, audio_file_5
                ] if audio_file is not None
            ]
            pannings = self._extract_values(tool_parameters.get("pannings", "0.0:0.0:0.0:0.0:0.0"))
            volume_ratios = self._extract_values(tool_parameters.get("volume_ratios", "1.0:1.0:1.0:1.0:1.0"))
            if len(audio_files) > len(pannings) or len(audio_files) > len(volume_ratios):
                raise ToolProviderCredentialValidationError(
                    f"Number of audio files ({len(audio_files)}) "
                    f"exceeds the number of panning values ({len(pannings)}) "
                    f"or volume ratio values ({len(volume_ratios)})."
                )
            output_format = tool_parameters.get("output_format", "mp3")

            # 1) load audio files and agjust panning and volume
            segments = []
            for idx, file in enumerate(audio_files):
                file_format = file.extension.lstrip(".")
                seg = AudioSegment.from_file(io.BytesIO(file.blob), format=file_format).set_channels(2)
                seg = seg + self._convert_ratio_to_db(volume_ratios[idx])
                seg = seg.pan(pannings[idx])
                segments.append(seg)

            # 2) align lengths
            max_len = max([len(seg) for seg in segments]) if segments else 0
            padded_segments = [seg.append(AudioSegment.silent(duration=max_len - len(seg)), crossfade=0) if len(seg) < max_len else seg for seg in segments]

            # 3) mix segments
            mixed = padded_segments[0]
            for seg in padded_segments[1:]:
                mixed = mixed.overlay(seg)

            # export the final mixed audio
            buffer = io.BytesIO()
            if output_format == "wav":
                mixed.export(buffer, format=output_format, parameters=["-ar", "44100"])
            elif output_format == "mp3":
                mixed.export(buffer, format=output_format, parameters=["-ar", "44100"], bitrate="160k")
            yield self.create_blob_message(blob=buffer.getvalue(), meta={"mime_type": self._get_mime_type(output_format)})

        except Exception as e:
            raise ToolProviderCredentialValidationError(f"Error generating mixed audio: {str(e)}")
