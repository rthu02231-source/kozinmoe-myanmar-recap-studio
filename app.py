import streamlit as st
import subprocess
import tempfile
import os
import imageio_ffmpeg

st.set_page_config(
    page_title="KOZINMOE Myanmar Recap Studio",
    page_icon="🎬",
    layout="wide"
)

st.title("KOZINMOE Myanmar Recap Studio")
st.caption("AI Video Recap • Burmese TTS • Subtitles")

st.header("1. Video Upload")

video = st.file_uploader(
    "ဗီဒီယိုဖိုင် ရွေးချယ်ပါ",
    type=["mp4", "mov", "mkv", "webm"]
)

st.header("2. Video Settings")

resolution = st.selectbox(
    "Resolution",
    ["720p", "1080p"]
)

ratio = st.selectbox(
    "Video Ratio",
    ["9:16", "16:9", "1:1", "4:3", "3:4"]
)

mute_original = st.checkbox(
    "မူရင်းအသံပိတ်ရန်",
    value=True
)

blur_enabled = st.checkbox(
    "Blur ဖွင့်ရန်",
    value=False
)

blur_strength = st.slider(
    "Blur Strength",
    1, 20, 5
)

st.header("3. Burmese Subtitles")

subtitle_enabled = st.checkbox(
    "မြန်မာစာတန်းထိုး ဖွင့်ရန်",
    value=False
)

subtitle_text = st.text_area(
    "မြန်မာစာသား",
    placeholder="မြန်မာစာသားကို ဒီမှာ ထည့်ပါ..."
)

st.caption(
    "မြန်မာစာတန်းထိုးအတွက် Font နှင့် Rendering ကို "
    "နောက်အဆင့်တွင် ချိတ်ဆက်ပါမည်။"
)

st.header("4. Gemini Burmese TTS")

voice = st.selectbox(
    "Narrator",
    [
        "သီဟ (အမျိုးသားအသံ)",
        "နီလာ (အမျိုးသမီးအသံ)"
    ]
)

narration = st.text_area(
    "အသံထုတ်ရန် ဇာတ်ကြောင်း",
    placeholder="မြန်မာဇာတ်ကြောင်းကို ဒီမှာ ရေးပါ..."
)

st.info(
    "Gemini TTS ကို နောက်အဆင့်တွင် ချိတ်ဆက်ပါမည်။"
)

st.header("5. Process & Export")

if st.button("Process Video & Export MP4", type="primary"):

    if video is None:
        st.error("အရင်ဆုံး Video ဖိုင် ရွေးချယ်ပါ။")

    else:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:

                input_path = os.path.join(
                    temp_dir, "input_video"
                )

                output_path = os.path.join(
                    temp_dir, "output.mp4"
                )

                with open(input_path, "wb") as f:
                    f.write(video.getvalue())

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

                width, height = dimensions[(resolution, ratio)]

                filters = [
                    f"scale={width}:{height}:"
                    "
