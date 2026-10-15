import os
import re
import subprocess
import tempfile
import wave

import streamlit as st
import imageio_ffmpeg
from google import genai
from google.genai import types


st.set_page_config(
    page_title="KOZINMOE Myanmar Recap Studio",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 KOZINMOE Myanmar Recap Studio")
st.caption("Myanmar AI Voice • Auto Subtitle • Zoom Frame • MP4 Export")

video = st.file_uploader(
    "ဗီဒီယိုဖိုင် ရွေးပါ",
    type=["mp4", "mov", "mkv", "webm"],
)

resolution = st.selectbox(
    "Resolution",
    ["720p", "1080p"],
)

ratio = st.selectbox(
    "Video Ratio",
    ["9:16", "16:9", "1:1", "4:3", "3:4"],
)

mute_original = st.checkbox(
    "မူရင်းအသံပိတ်ရန်",
    value=True,
)

blur_enabled = st.checkbox(
    "Blur ဖွင့်ရန်",
    value=False,
)

blur_strength = st.slider(
    "Blur Strength",
    1,
    20,
    5,
)

st.header("🎙️ Gemini Burmese TTS")

voice = st.selectbox(
    "Narrator",
    [
        "သီဟ (အမျိုးသားအသံ)",
        "နီလာ (အမျိုးသမီးအသံ)",
    ],
)

narration = st.text_area(
    "ဇာတ်ကြောင်း",
    placeholder="မြန်မာဇာတ်ကြောင်း ရေးပါ...",
    height=180,
)

st.header("📝 Subtitle Settings")

subtitle_enabled = st.checkbox(
    "ဗီဒီယိုပေါ် စာတန်းထိုးရန်",
    value=True,
)

subtitle_font_size = st.slider(
    "စာတန်းအရွယ်အစား",
    20,
    60,
    38,
)

st.header("🔎 Zoom Frame")

zoom_enabled = st.checkbox(
    "Zoom Effect ဖွင့်ရန်",
    value=True,
)

zoom_amount = st.slider(
    "Zoom အား",
    1.0,
    1.5,
    1.15,
    0.05,
)

dimensions = {
    ("720p", "9:16"): (720, 1280),
    ("720p", "16:9"): (1280, 720),
    ("720p", "1:1"): (720, 720),
    ("720p", "4:3"): (960, 720),
    ("720p", "3:4"): (720, 960),
    ("1080p", "9:16"): (1080, 1920),
    ("1080p", "16:9"): (1920, 1080),
    ("1080p", "1:1"): (1080, 1080),
    ("1080p", "4:3"): (1440, 1080),
    ("1080p", "3:4"): (1080, 1440),
}


def run_ffmpeg(command, timeout=1800):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2500:])

    return result


def make_subtitle(text, duration, path):
    """Create basic timed subtitles from the supplied narration."""
    sentences = re.split(r"(?<=[။!?])\s*", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return

    # Allocate time proportionally to sentence length.
    weights = [max(len(s), 1) for s in sentences]
    total_weight = sum(weights)
    current = 0.0

    def stamp(seconds):
        milliseconds = int(seconds * 1000)
        hours, milliseconds = divmod(milliseconds, 3600000)
        minutes, milliseconds = divmod(milliseconds, 60000)
        seconds, milliseconds = divmod(milliseconds, 1000)
        return (
            f"{hours:02}:{minutes:02}:"
            f"{seconds:02},{milliseconds:03}"
        )

    with open(path, "w", encoding="utf-8-sig") as file:
        for index, sentence in enumerate(sentences, start=1):
            start = current
            current += duration * (
                weights[index - 1] / total_weight
            )

            # Escape the SRT separator sequence if present.
            sentence = sentence.replace("-->", "→")

            file.write(
                f"{index}\n"
                f"{stamp(start)} --> {stamp(current)}\n"
                f"{sentence}\n\n"
            )


if st.button("🚀 Process Video & Export MP4", type="primary"):

    if video is None:
        st.error("အရင်ဆုံး Video ရွေးပါ။")

    elif not narration.strip():
        st.error("ဇာတ်ကြောင်း ထည့်ပါ။")

    else:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]

            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = os.path.join(temp_dir, "input.mp4")
                audio_path = os.path.join(temp_dir, "narration.wav")
                subtitle_path = os.path.join(temp_dir, "captions.srt")
                output_path = os.path.join(temp_dir, "output.mp4")

                with open(input_path, "wb") as file:
                    file.write(video.getvalue())

                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

                client = genai.Client(api_key=api_key)

                voice_name = (
                    "Kore" if voice.startswith("သီဟ") else "Puck"
                )

                st.info("အဆင့် ၁ — AI အသံထုတ်နေပါသည်။")

                response = client.models.generate_content(
                    model="gemini-2.5-flash-preview-tts",
                    contents=(
                        "Read the following Burmese text aloud "
                        "clearly and naturally:\n" + narration
                    ),
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=(
                                    types.PrebuiltVoiceConfig(
                                        voice_name=voice_name
                                    )
                                )
                            )
                        ),
                    ),
                )

                audio_data = None

                for candidate in response.candidates or []:
                    for part in candidate.content.parts or []:
                        if part.inline_data and part.inline_data.data:
                            audio_data = part.inline_data.data
                            break
                    if audio_data is not None:
                        break

                if audio_data is None:
                    raise RuntimeError(
                        "Gemini မှ အသံဒေတာ မရရှိပါ။"
                    )

                with wave.open(audio_path, "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(24000)
                    wav.writeframes(audio_data)

                with wave.open(audio_path, "rb") as wav:
                    audio_duration = (
                        wav.getnframes() / wav.getframerate()
                    )

                if subtitle_enabled:
                    make_subtitle(
                        narration,
                        audio_duration,
                        subtitle_path,
                    )

                width, height = dimensions[(resolution, ratio)]

                filters = [
                    (
                        f"scale={width}:{height}:"
                        "force_original_aspect_ratio=increase"
                    ),
                    f"crop={width}:{height}",
                ]

                if zoom_enabled:
                    filters.extend([
                        "scale=iw*1.08:ih*1.08",
                        f"crop={width}:{height}",
                    ])

                if blur_enabled:
                    filters.append(
                        f"boxblur={blur_strength}:1"
                    )

                if subtitle_enabled:
                    # Requires a suitable Unicode font on the server.
                    subtitle_filter = (
                        f"subtitles='{subtitle_path}':"
                        f"force_style='FontSize={subtitle_font_size},"
                        "PrimaryColour=&H0000FFFF,"
                        "OutlineColour=&H00000000,"
                        "BorderStyle=1,Outline=3,"
                        "Alignment=2,MarginV=45'"
                    )
                    filters.append(subtitle_filter)

                command = [
                    ffmpeg,
                    "-y",
                    "-i", input_path,
                    "-i", audio_path,
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-vf", ",".join(filters),
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "23",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-af", "apad",
                    "-t", str(audio_duration),
                    "-movflags", "+faststart",
                    "-threads", "2",
                    output_path,
                ]

                st.info("အဆင့် ၂ — ဗီဒီယိုတည်းဖြတ်နေပါသည်။")

                run_ffmpeg(command)

                with open(output_path, "rb") as file:
                    output_bytes = file.read()

                st.success("MP4 ထုတ်လုပ်ပြီးပါပြီ။")
                st.video(output_bytes)

                st.download_button(
                    "⬇️ Download MP4",
                    data=output_bytes,
                    file_name="kozinmoe_recap.mp4",
                    mime="video/mp4",
                )

        except KeyError:
            st.error(
                "GEMINI_API_KEY မတွေ့ပါ။ Streamlit Secrets ကို စစ်ပါ။"
            )

        except subprocess.TimeoutExpired:
            st.error("Video ပြုလုပ်ချိန် ကြာလွန်းနေပါသည်။")

        except Exception as error:
            st.error(f"Error: {error}")
