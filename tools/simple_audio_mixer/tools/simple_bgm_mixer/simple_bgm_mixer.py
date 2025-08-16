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
            # param: audio files
            voice_file = tool_parameters.get("voice_file")
            bgm_file = tool_parameters.get("bgm_file")

            # param: durations
            a_bgm_intro_fadein_ms = tool_parameters.get("a_bgm_intro_fadein_ms", 100)
            b_bgm_intro_play_ms = tool_parameters.get("b_bgm_intro_play_ms", 5000)
            c_bgm_intro_fadeout_ms = tool_parameters.get("c_bgm_intro_fadeout_ms", 1000)
            d_bgm_pre_voice_delay_ms = tool_parameters.get("d_bgm_pre_voice_delay_ms", 500)
            e_bgm_post_voice_delay_ms = tool_parameters.get("e_bgm_post_voice_delay_ms", 1000)
            f_bgm_outro_fadein_ms = tool_parameters.get("f_bgm_outro_fadein_ms", 1000)
            g_bgm_outro_play_ms = tool_parameters.get("g_bgm_outro_play_ms", 5000)
            h_bgm_outro_fadeout_ms = tool_parameters.get("h_bgm_outro_fadeout_ms", 5000)
    
            # param: volume ratios
            i_voice_volume_ratio = tool_parameters.get("i_voice_volume_ratio", 1.0)
            j_bgm_intro_volume_ratio = tool_parameters.get("j_bgm_intro_volume_ratio", 1.0)
            k_bgm_during_voice_volume_ratio = tool_parameters.get("k_bgm_during_voice_volume_ratio", 0.2)
            l_bgm_outro_volume_ratio = tool_parameters.get("l_bgm_outro_volume_ratio", 1.0)
            z_master_volume_ratio = tool_parameters.get("z_master_volume_ratio", 1.0)
    
            # param: output format
            output_format = tool_parameters.get("output_format", "mp3")

            # load audio files
            voice_format = voice_file.extension.lstrip(".")
            bgm_format = bgm_file.extension.lstrip(".")
            voice = AudioSegment.from_file(io.BytesIO(voice_file.blob), format=voice_format)
            bgm = AudioSegment.from_file(io.BytesIO(bgm_file.blob), format=bgm_format)
            if voice.channels == 1:
                voice = voice.set_channels(2)
            if bgm.channels == 1:
                bgm = bgm.set_channels(2)

            # calc durations and make bgm long enough
            intro_duration = a_bgm_intro_fadein_ms + b_bgm_intro_play_ms + c_bgm_intro_fadeout_ms + d_bgm_pre_voice_delay_ms
            outro_duration = f_bgm_outro_fadein_ms + g_bgm_outro_play_ms + h_bgm_outro_fadeout_ms + e_bgm_post_voice_delay_ms
            total_duration = intro_duration + len(voice) + outro_duration
            bgm = bgm * (total_duration // len(bgm) + 1)

            # construct bgm
            # 1) intro, fade-in
            intro_fadein = bgm[:a_bgm_intro_fadein_ms].fade_in(a_bgm_intro_fadein_ms).apply_gain(self._convert_ratio_to_db(j_bgm_intro_volume_ratio))
            # 2) intro, play
            _start_intro_play = a_bgm_intro_fadein_ms
            _end_intro_play = _start_intro_play + b_bgm_intro_play_ms
            intro_play = bgm[_start_intro_play:_end_intro_play].apply_gain(self._convert_ratio_to_db(j_bgm_intro_volume_ratio))
            # 3) intro, fade-out
            _start_intro_fadeout = _end_intro_play
            _end_intro_fadeout = _start_intro_fadeout + c_bgm_intro_fadeout_ms
            intro_fadeout = bgm[_start_intro_fadeout:_end_intro_fadeout].fade(
                from_gain=self._convert_ratio_to_db(j_bgm_intro_volume_ratio),
                to_gain=self._convert_ratio_to_db(k_bgm_during_voice_volume_ratio),
                start=0,
                duration=c_bgm_intro_fadeout_ms
            )
            # 4) intro, pre-voice delay
            _start_pre_voice_delay = _end_intro_fadeout
            _end_pre_voice_delay = _start_pre_voice_delay + d_bgm_pre_voice_delay_ms
            pre_voice_delay = bgm[_start_pre_voice_delay:_end_pre_voice_delay].apply_gain(self._convert_ratio_to_db(k_bgm_during_voice_volume_ratio))
            # 5) voice
            _start_voice = _end_pre_voice_delay
            _end_voice = _start_voice + len(voice)
            voice_section = bgm[_start_voice:_end_voice].apply_gain(self._convert_ratio_to_db(k_bgm_during_voice_volume_ratio))
            # 6) outro, post-voice delay
            _start_post_voice_delay = _end_voice
            _end_post_voice_delay = _start_post_voice_delay + e_bgm_post_voice_delay_ms
            post_voice_delay = bgm[_start_post_voice_delay:_end_post_voice_delay].apply_gain(self._convert_ratio_to_db(k_bgm_during_voice_volume_ratio))
            # 7) outro, fade-in
            _start_outro_fadein = _end_post_voice_delay
            _end_outro_fadein = _start_outro_fadein + f_bgm_outro_fadein_ms
            outro_fadein = bgm[_start_outro_fadein:_end_outro_fadein].fade(
                from_gain=self._convert_ratio_to_db(k_bgm_during_voice_volume_ratio),
                to_gain=self._convert_ratio_to_db(l_bgm_outro_volume_ratio),
                start=0,
                duration=f_bgm_outro_fadein_ms
            )
            # 8) outro, play
            _start_outro_play = _end_outro_fadein
            _end_outro_play = _start_outro_play + g_bgm_outro_play_ms
            outro_play = bgm[_start_outro_play:_end_outro_play].apply_gain(self._convert_ratio_to_db(l_bgm_outro_volume_ratio))
            # 9) outro, fade-out
            _start_outro_fadeout = _end_outro_play
            _end_outro_fadeout = _start_outro_fadeout + h_bgm_outro_fadeout_ms
            outro_fadeout = bgm[_start_outro_fadeout:_end_outro_fadeout].fade_out(h_bgm_outro_fadeout_ms).apply_gain(self._convert_ratio_to_db(l_bgm_outro_volume_ratio))
            # 10) combine all sections
            bgm_final = intro_fadein + intro_play + intro_fadeout + pre_voice_delay + voice_section + post_voice_delay + outro_fadein + outro_play + outro_fadeout

            # mix voice with bgm
            mixed = bgm_final.overlay(voice.apply_gain(self._convert_ratio_to_db(i_voice_volume_ratio)), position=intro_duration)

            # apply master volume
            mixed = mixed.apply_gain(self._convert_ratio_to_db(z_master_volume_ratio))

            # export the final mixed audio
            buffer = io.BytesIO()
            if output_format == "wav":
                mixed.export(buffer, format=output_format, parameters=["-ar", "44100"])
            elif output_format == "mp3":
                mixed.export(buffer, format=output_format, parameters=["-ar", "44100"], bitrate="160k")
            yield self.create_blob_message(blob=buffer.getvalue(), meta={"mime_type": self._get_mime_type(output_format)})

        except Exception as e:
            raise ToolProviderCredentialValidationError(f"Error generating mixed audio: {str(e)}")
