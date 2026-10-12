import os
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

st.title("KOZINMOE Myanmar Recap Studio")
st.caption("Burmese AI Voice • Video Processing • MP4 Export")


video = st.file_uploader(
    "ဗီဒီယိုဖိုင် ရွေးချယ်ပါ",
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
    min_value=1,
    max_value=20,
    value=5,
)

st.header("Gemini Burmese TTS")

voice = st.selectbox(
    "Narrator",
    [
        "သီဟ (အမျိုးသားအသံ)",
        "နီလာ (အမျိုးသမီးအသံ)",
    ],
)

narration = st.text_area(
    "အသံထုတ်ရန် ဇာတ်ကြောင်း",
    placeholder="မြန်မာဇာတ်ကြောင်းကို ဒီနေရာမှာ ရေးပါ...",
)

st.header("Process & Export")


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


if st.button("Process Video & Export MP4", type="primary"):

    if video is None:
        st.error("အရင်ဆုံး Video ဖိုင် ရွေးချယ်ပါ။")

    elif not narration.strip():
        st.error("အသံထုတ်ရန် ဇာတ်ကြောင်း ထည့်ပါ။")

    else:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]

            with tempfile.TemporaryDirectory() as temp_dir:

                input_path = os.path.join(
                    temp_dir,
                    "input_video",
                )

                audio_path = os.path.join(
                    temp_dir,
                    "narration.wav",
                )

                output_path = os.path.join(
                    temp_dir,
                    "kozinmoe_recap.mp4",
                )

                with open(input_path, "wb") as file:
                    file.write(video.getvalue())

                client = genai.Client(
                    api_key=api_key,
                )

                voice_name = (
                    "Kore"
                    if voice.startswith("သီဟ")
                    else "Puck"
                )

                st.info("အဆင့် ၁/၂ — Gemini အသံထုတ်နေပါသည်။")

                response = client.models.generate_content(
                    model="gemini-2.5-flash-preview-tts",
                    contents=(
                        "Read the following Burmese text aloud "
                        "clearly and naturally. Preserve the "
                        "original Burmese words:\n"
                        + narration
                    ),
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=(
                                    types.PrebuiltVoiceConfig(
                                        voice_name=voice_name,
                                    )
                                )
                            )
                        ),
                    ),
                )

                audio_data = None

                for candidate in response.candidates or []:
                    for part in candidate.content.parts or []:
                        if part.inline_data is not None:
                            if part.inline_data.data is not None:
                                audio_data = part.inline_data.data
                                break

                    if audio_data is not None:
                        break

                if audio_data is None:
                    raise RuntimeError(
                        "Gemini က အသံဒေတာ မထုတ်ပေးပါ။"
                    )

                with wave.open(audio_path, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(24000)
                    wav_file.writeframes(audio_data)

                width, height = dimensions[
                    (resolution, ratio)
                ]

                video_filters = [
                    (
                        f"scale={width}:{height}:"
                        "force_original_aspect_ratio=increase"
                    ),
                    f"crop={width}:{height}",
                ]

                if blur_enabled:
                    video_filters.append(
                        f"boxblur={blur_strength}:1"
                    )

                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

                command = [
                    ffmpeg,
                    "-y",
                    "-i", input_path,
                    "-i", audio_path,
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-vf", ",".join(video_filters),
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "23",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-af", "apad",
                    "-shortest",
                    "-movflags", "+faststart",
                    "-threads", "2",
                    output_path,
                ]

                st.info("အဆင့် ၂/၂ — ဗီဒီယိုနဲ့ အသံ ပေါင်းနေပါသည်။")

                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=1800,
                )

                if result.returncode != 0:
                    st.error("MP4 ထုတ်ရာတွင် Error ဖြစ်နေပါသည်။")
                    st.code(result.stderr[-3000:])

                else:
                    with open(output_path, "rb") as file:
                        output_bytes = file.read()

                    st.success("MP4 ထုတ်လုပ်ပြီးပါပြီ။")
                    st.video(output_bytes)

                    st.download_button(
                        label="Download MP4",
                        data=output_bytes,
                        file_name="kozinmoe_recap.mp4",
                        mime="video/mp4",
                    )

        except KeyError:
            st.error(
                "GEMINI_API_KEY မတွေ့ပါ။ "
                "Streamlit Secrets ကို စစ်ဆေးပါ။"
            )

        except subprocess.TimeoutExpired:
            st.error(
                "Video ပြုပြင်ချိန် ကြာလွန်းနေပါသည်။ "
                "ပိုတိုသော Video ဖြင့် စမ်းပါ။"
            )

        except Exception as error:
            st.error(f"Error: {error}")
