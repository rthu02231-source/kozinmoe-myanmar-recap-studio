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

video = st.file_uploader(
    "ဗီဒီယိုဖိုင် ရွေးချယ်ပါ",
    type=["mp4", "mov", "mkv", "webm"]
)

resolution = st.selectbox("Resolution", ["720p", "1080p"])
ratio = st.selectbox("Video Ratio", ["9:16", "16:9", "1:1", "4:3", "3:4"])
mute_original = st.checkbox("မူရင်းအသံပိတ်ရန်", value=True)
blur_enabled = st.checkbox("Blur ဖွင့်ရန်", value=False)
blur_strength = st.slider("Blur Strength", 1, 20, 5)

st.header("မြန်မာစာတန်းထိုး")
subtitle_enabled = st.checkbox("မြန်မာစာတန်းထိုး ဖွင့်ရန်", value=False)
subtitle_text = st.text_area("မြန်မာစာသား")
font_size = st.slider("စာတန်းအရွယ်အစား", 20, 60, 40)

st.header("Gemini Burmese TTS")
voice = st.selectbox("Narrator", ["သီဟ (အမျိုးသားအသံ)", "နီလာ (အမျိုးသမီးအသံ)"])
narration = st.text_area("အသံထုတ်ရန် ဇာတ်ကြောင်း")

st.header("Process & Export")

if st.button("Process Video & Export MP4", type="primary"):
    if video is None:
        st.error("အရင်ဆုံး Video ဖိုင် ရွေးချယ်ပါ။")
    else:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = os.path.join(temp_dir, "input_video")
                output_path = os.path.join(temp_dir, "output.mp4")

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
                    f"scale={width}:{height}:force_original_aspect_ratio=increase",
                    f"crop={width}:{height}"
                ]

                if blur_enabled:
                    filters.append(f"boxblur={blur_strength}:1")

                command = [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-y", "-i", input_path,
                    "-vf", ",".join(filters),
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "23",
                    "-pix_fmt", "yuv420p",
                    "-threads", "2"
                ]

                if mute_original:
                    command.append("-an")
                else:
                    command.extend(["-c:a", "aac", "-b:a", "128k"])

                command.extend(["-movflags", "+faststart", output_path])

                with st.spinner("Video ပြုပြင်နေပါသည်။ ခဏစောင့်ပါ..."):
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=1800
                    )

                if result.returncode != 0:
                    st.error("Video ပြုပြင်ရာတွင် Error ဖြစ်နေပါသည်။")
                    st.code(result.stderr[-2500:])
                else:
                    with open(output_path, "rb") as f:
                        output_bytes = f.read()

                    st.success("Video ပြုပြင်ပြီးပါပြီ။")
                    st.video(output_bytes)
                    st.download_button(
                        "Download MP4",
                        data=output_bytes,
                        file_name="kozinmoe_recap.mp4",
                        mime="video/mp4"
                    )

        except subprocess.TimeoutExpired:
            st.error("လုပ်ဆောင်ချိန်ကြာလွန်းနေပါသည်။ Video ပိုတိုတာနဲ့ စမ်းပါ။")
        except Exception as e:
            st.error(f"Error: {e}")

st.warning(
    "လက်ရှိတွင် Video Processing နှင့် MP4 Export ကိုသာ ချိတ်ဆက်ထားပါသည်။ "
    "Gemini TTS၊ မြန်မာစာတန်းထိုး Rendering နှင့် Freeze Frame/Zoom များ "
    "အလုပ်လုပ်ရန် ထပ်မံချိတ်ဆက်ရပါမည်။"
)
