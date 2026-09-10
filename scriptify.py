import io
import streamlit as st

# ----------------- Safe Imports for Dependencies -----------------
# 1. Indic Transliteration
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
    HAS_INDIC = True
except ImportError:
    HAS_INDIC = False

# 2. Google Text-to-Speech (gTTS)
try:
    from gTTS import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False
    gTTS = None

# 3. Optical Character Recognition (OCR) & Imaging
try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    pytesseract = None

# 4. Document Handling
try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


# ----------------- Script & Language Mappings -----------------
if HAS_INDIC:
    SCRIPT_CODES = {
        "Devanagari (Hindi)": sanscript.DEVANAGARI,
        "Bengali": sanscript.BENGALI,
        "Gurmukhi (Punjabi)": sanscript.GURMUKHI,
        "Gujarati": sanscript.GUJARATI,
        "Oriya": sanscript.ORIYA,
        "Tamil": sanscript.TAMIL,
        "Telugu": sanscript.TELUGU,
        "Kannada": sanscript.KANNADA,
        "Malayalam": sanscript.MALAYALAM,
        "Latin (ITRANS/English)": sanscript.ITRANS
    }
else:
    SCRIPT_CODES = {}

TTS_LANG_MAP = {
    "Devanagari (Hindi)": "hi",
    "Bengali": "bn",
    "Gurmukhi (Punjabi)": "pa",
    "Gujarati": "gu",
    "Oriya": "or",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Latin (ITRANS/English)": "en"
}


# ----------------- Helper Processing Functions -----------------
def extract_text_from_image(uploaded_image):
    if not HAS_OCR:
        st.warning("⚠️ `pytesseract` or `Pillow` is not installed. Image OCR processing is unavailable.")
        return ""
    try:
        img = Image.open(uploaded_image)
        try:
            text = pytesseract.image_to_string(img, lang="eng+hin+tam+tel+kan+mal+ben+guj+ori+pan")
        except Exception:
            text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        st.error(f"Error reading image file: {e}")
        return ""

def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        if not HAS_DOCX:
            st.warning("⚠️ `python-docx` is not installed. DOCX file processing is unavailable.")
            return ""
        document = docx.Document(uploaded_file)
        return "\n".join([p.text for p in document.paragraphs])
    elif uploaded_file.type == "application/pdf":
        if not HAS_PDF:
            st.warning("⚠️ `PyPDF2` is not installed. PDF file processing is unavailable.")
            return ""
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        return "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    return ""

def auto_detect_script(text):
    for ch in text:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F: return "Devanagari (Hindi)"
        elif 0x0980 <= cp <= 0x09FF: return "Bengali"
        elif 0x0A00 <= cp <= 0x0A7F: return "Gurmukhi (Punjabi)"
        elif 0x0A80 <= cp <= 0x0AFF: return "Gujarati"
        elif 0x0B00 <= cp <= 0x0B7F: return "Oriya"
        elif 0x0B80 <= cp <= 0x0BFF: return "Tamil"
        elif 0x0C00 <= cp <= 0x0C7F: return "Telugu"
        elif 0x0C80 <= cp <= 0x0CFF: return "Kannada"
        elif 0x0D00 <= cp <= 0x0D7F: return "Malayalam"
    return "Latin (ITRANS/English)"

def text_to_speech(text, lang="hi"):
    if not HAS_GTTS:
        st.warning("⚠️ `gTTS` library is not loaded. Audio output playback is disabled.")
        return None
    try:
        tts = gTTS(text=text, lang=lang)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except Exception as e:
        st.error(f"Audio generation failed: {e}")
        return None


# ----------------- Streamlit UI Setup -----------------
st.set_page_config(page_title="Scriptify - Multilingual Street Sign Transliteration", layout="wide")
st.title("📜 Scriptify: Multilingual Street Sign Transliteration")

st.markdown("""
Convert street sign text across major Indian scripts while maintaining phonetic pronunciation across native languages.
""")

if not HAS_INDIC:
    st.error("❌ Critical package `indic_transliteration` is missing. Please run `python -m pip install indic_transliteration` in your terminal.")
    st.stop()

# ----------------- Input Mode Selection -----------------
input_choice = st.radio("Select Input Mode", ["Text Entry", "Image OCR", "Document Upload"], horizontal=True)
input_text = ""

if input_choice == "Text Entry":
    input_text = st.text_area("Enter Indian script or Latin phonetic text", height=130, placeholder="e.g., Chennai or சென்னை or चेन्नई")
elif input_choice == "Image OCR":
    uploaded_image = st.file_uploader("Upload Street Sign Image", type=["jpg", "png", "jpeg"])
    if uploaded_image:
        input_text = extract_text_from_image(uploaded_image)
        st.text_area("Extracted Text from OCR", input_text, height=130)
elif input_choice == "Document Upload":
    uploaded_file = st.file_uploader("Upload File", type=["txt", "docx", "pdf"])
    if uploaded_file:
        input_text = extract_text_from_file(uploaded_file)
        st.text_area("Extracted Document Content", input_text, height=130)

# ----------------- Script Detection & Selection -----------------
if input_text.strip():
    detected_script = auto_detect_script(input_text)
    st.info(f"🔎 Detected Source Script: **{detected_script}**")
else:
    detected_script = list(SCRIPT_CODES.keys())[0]

col1, col2 = st.columns(2)
with col1:
    src_script_name = st.selectbox(
        "Source Script", 
        list(SCRIPT_CODES.keys()), 
        index=list(SCRIPT_CODES.keys()).index(detected_script) if detected_script in SCRIPT_CODES else 0
    )
with col2:
    tgt_script_name = st.selectbox("Target Script", list(SCRIPT_CODES.keys()), index=1)

# ----------------- Transliteration & Output -----------------
if st.button("Transliterate", type="primary"):
    if not input_text.strip():
        st.warning("⚠️ Please input text or upload a file first.")
    elif src_script_name == tgt_script_name:
        st.info("ℹ️ Source and Target scripts are identical. Select a different Target script.")
    else:
        try:
            output_text = transliterate(input_text, SCRIPT_CODES[src_script_name], SCRIPT_CODES[tgt_script_name])
            st.success("✅ Transliteration Successful!")
            st.text_area("Transliterated Text Output", output_text, height=130)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                st.download_button(
                    label="⬇️ Download Text Result", 
                    data=output_text, 
                    file_name="transliterated_output.txt", 
                    mime="text/plain"
                )

            # Audio Pronunciation
            tts_lang = TTS_LANG_MAP.get(tgt_script_name, "en")
            audio_data = text_to_speech(output_text, tts_lang)
            if audio_data:
                st.audio(audio_data, format="audio/mp3")
                with btn_col2:
                    st.download_button(
                        label="⬇️ Download Audio (MP3)", 
                        data=audio_data, 
                        file_name="speech_output.mp3", 
                        mime="audio/mpeg"
                    )
        except Exception as err:
            st.error(f"❌ Transliteration error: {err}")