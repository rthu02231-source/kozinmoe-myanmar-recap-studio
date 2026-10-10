import streamlit as st

st.set_page_config(
    page_title="KOZINMOE Myanmar Recap Studio",
    page_icon="🎬",
    layout="wide"
)

st.title("KOZINMOE Myanmar Recap Studio")
st.caption("AI Video Recap • Burmese TTS • Subtitles")

st.divider()

st.header("1. Video Upload")

video = st.file_uploader(
    "ဗီဒီယိုဖိုင် ရွေးချယ်ပါ",
    type=["mp4", "mov", "mkv", "webm"]
)

if video:
    st.video(video)
    st.success(f"ရွေးချယ်ထားသောဖိုင်: {video.name}")

st.info(
    "Video အရှည်ကို App ဘက်မှ မကန့်သတ်ထားပါ။ "
    "လက်တွေ့လုပ်ဆောင်နိုင်မှုသည် Hosting စွမ်းဆောင်ရည်ပေါ် မူတည်ပါမည်။"
)

st.divider()

st.header("2. Video Settings")

col1, col2 = st.columns(2)

with col1:
    resolution = st.selectbox(
        "Resolution",
        ["720p", "1080p"]
    )

    ratio = st.selectbox(
        "Video Ratio",
        ["9:16", "16:9", "1:1", "4:3", "3:4"]
    )

with col2:
    mute_original = st.checkbox(
        "မူရင်းအသံပိတ်ရန်",
        value=True
    )

    blur_enabled = st.checkbox(
        "Blur ဖွင့်ရန်",
        value=False
    )

    blur_strength = st.slider(
        "Blur Size / Strength",
        1, 50, 15
    )

with st.expander("Freeze Frame & Zoom Settings"):
    freeze_interval = st.slider(
        "Freeze Frame Interval (seconds)",
        1, 30, 4
    )

    freeze_duration = st.slider(
        "Freeze Frame Duration (seconds)",
        1, 15, 7
    )

    zoom_power = st.slider(
        "Zoom Power",
        1.0, 3.0, 1.5, 0.1
    )

st.divider()

st.header("3. Burmese Subtitles")

subtitle_enabled = st.checkbox(
    "မြန်မာစာတန်းထိုး ဖွင့်ရန်",
    value=True
)

subtitle_text = st.text_area(
    "မြန်မာစာသား",
    placeholder="မြန်မာစာသားကို ဒီမှာ ထည့်ပါ..."
)

font_size = st.slider(
    "စာတန်းအရွယ်အစား (px)",
    20, 60, 40
)

st.caption("Font: Pyidaungsu — စာတန်းထိုးရန် Font ဖိုင်လိုအပ်ပါမည်။")

st.divider()

st.header("4. Gemini Burmese TTS")

voice = st.selectbox(
    "Narrator",
    [
        "သီဟ (အမျိုးသားအသံ)",
        "နီလာ (အမျိုးသမီးအသံ)"
    ]
)

speed = st.select_slider(
    "Voice Speed",
    options=["အနှေး", "ပုံမှန်", "အမြန်"],
    value="ပုံမှန်"
)

narration = st.text_area(
    "အသံထုတ်ရန် ဇာတ်ကြောင်း",
    placeholder="မြန်မာဇာတ်ကြောင်းကို ဒီမှာ ရေးပါ..."
)

st.button(
    "Generate Burmese Voice",
    type="primary",
    disabled=not bool(narration.strip())
)

st.divider()

st.header("5. Export")

st.write(f"Resolution: {resolution}")
st.write(f"Video Ratio: {ratio}")

st.warning(
    "ဒီအဆင့်မှာ Website မျက်နှာပြင်ကိုသာ တည်ဆောက်ထားပါတယ်။ "
    "TTS ထုတ်လုပ်ခြင်း၊ Video Effects ပေါင်းစပ်ခြင်းနဲ့ "
    "MP4 Export ကို နောက်အဆင့်မှာ ချိတ်ဆက်ရပါမယ်။"
)
