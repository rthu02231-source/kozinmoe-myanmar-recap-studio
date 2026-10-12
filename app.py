import streamlit as st
import subprocess
import tempfile
import os
import wave
import imageio_ffmpeg
from google import genai
from google.genai import types

st.set_page_config(
    page_title="KOZINMOE Myanmar Recap Studio",
    page_icon="🎬",
    layout="wide"
)

st.title("KOZINMOE Myanmar Recap Studio")
st.caption("AI Video Recap • Burmese TTS • MP4 Export")

video = st.file_uploader(
    "ဗီဒီယိုဖိုင် ရွေးချယ်ပါ",
    type=["mp4", "mov", "mkv", "webm"]
)

resolution = st.selectbox("Resolution", ["720p", "1080p"])

ratio = st.selectbox(
    "Video Ratio",
    ["9:16", "16:9", "1:1", "4:3", "3:4"]
)

mute_original = st.checkbox(
    "မူရင်းအသံပိတ်ရန်",
    value=True
)

blur_enabled = st.checkbox("Blur ဖွင့်ရန်", value=False)
blur_strength = st.slider("Blur Strength", 1, 20, 5)

st.header("Gemini Burmese TTS")

voice = st.selectbox(
    "Narrator",
    [
        "သီဟ (အမျိုးသားအသံ)",
        "နီလာ (အမျိုးသမီးအသံ)"
    ]
)

narration = st.text_area(
    "ဗီဒီယိုထဲ ထည့်မည့် ဇာတ်ကြောင်း",
    placeholder="ဒီနေရာမှာ မြန်မာစာသား ရိုက်ထည့်ပါ..."
)

st.info(
    "ဇာတ်ကြောင်းထည့်ထားပါက Gemini က အသံထုတ်ပြီး "
    "ဗီဒီယိုထဲ အလိုအလျောက်ပေါင်းထည့်ပေးပါမယ်။"
)

st.header("Process & Export")

if st.button("Process Video & Export MP4", type="primary"):

    if video is None:
        st.error("အရင်ဆုံး Video ဖိုင် ရွေးချယ်ပါ။")

    elif not narration.strip():
        st.error("အသံထုတ်ရန် မြန်မာဇာတ်ကြောင်း ထည့်ပါ။")

    else:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]

            with tempfile.TemporaryDirectory() as temp_dir:

                input_path = os.path.join(
                    temp_dir, "input_video"
                )
                audio_path = os.path.join(
                    temp_dir, "narration.wav"
                )
                output_path = os.path.join(
                    temp_dir, "kozinmoe_recap.mp4"
                )

                with open(input_path, "wb") as f:
                    f.write(video.getvalue())

                # 1. Gemini API ချိတ်ဆက်ခြင်း
                client = genai.Client(api_key=api_key)

                # UI ရှိ narrator ရွေးချယ်မှုကို အသံအမျိုးအစားနဲ့ချိတ်ခြင်း
                voice_name = (
                    "Kore"
                    if voice.startswith("သီဟ")
                    else "Puck"
                )

                # 2. မြန်မာစာမှ အသံထုတ်ခြင်း
                with st.spinner(
                    "Gemini က မြန်မာအသံ ထုတ်နေပါသည်..."
                ):
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-tts-preview",
                        contents=(
                            "Read the following Burmese text aloud "
                            "clearly and naturally. Preserve the "
                            "original Burmese words. "
                            "Text:\n" + narration
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
                            )
                        )
                    )

                audio_data = None

                for candidate in response.candidates or []:
                    for part in candidate.content.parts or []:
                        if part.inline_data and part.inline_data.data:
                            audio_data = part.inline_data.data
                            break
                    if audio_data:
                        break

                if not audio_data:
                    raise RuntimeError(
                        "Gemini မှ အသံဒေတာ မရရှိပါ။"
                    )

                # Gemini PCM အသံကို WAV အဖြစ်သိမ်းခြင်း
                with wave.open(audio_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(24000)
                    wf.writeframes(audio_data)

                # 3. Video အရွယ်အစားနှင့် Ratio သတ်မှတ်ခြင်း
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

                width, height = dimensions[
                    (resolution, ratio)
                ]

                filters = [
                    f"scale={width}:{height}:"
                    "force_original_aspect_ratio=increase",
                    f"crop={width}:{height}"
                ]

                if blur_enabled:
                    filters.append(
                        f"boxblur={blur_strength}:1"
                    )

                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

                # 4. Video နှင့် Gemini အသံ ပေါင်းခြင်း
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
                    "-shortest",
                    "-movflags", "+faststart",
                    "-threads", "2",
                    output_path
                ]

                with st.spinner(
                    "Video နဲ့ Gemini အသံကို ပေါင်းနေပါသည်..."
                ):
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=1800
                    )

                if result.returncode != 0:
                    st.error("Video Export မအောင်မြင်ပါ။")
                    st.code(result.stderr[-3000:])

                else:
                    with open(output_path, "rb") as f:
                        output_bytes = f.read()

                    st.success(
                        "Video နဲ့ Gemini အသံ ပေါင်းပြီးပါပြီ။"
                    )

                    st.video(output_bytes)

                    st.download_button(
                        label="Download MP4",
                        data=output_bytes,
                        file_name="kozinmoe_recap.mp4",
                        mime="video/mp4"
                    )
