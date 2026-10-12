import hashlib
import hmac
import html
import io
import json
import re
import threading
import time
import uuid
import wave
from datetime import datetime
from pathlib import Path

import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel

# ==========================================
# 1. CẤU HÌNH
# ==========================================

st.set_page_config(page_title="E-HERO AI", page_icon="🎧", layout="wide")

if "GEMINI_API_KEY" not in st.secrets:
    st.error(
        "Chưa cấu hình GEMINI_API_KEY. "
        "Thêm khóa vào mục Secrets của Streamlit Cloud."
    )
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Có thể đổi tên model trong Secrets mà không cần sửa code.
MODEL_CHAT = st.secrets.get("GEMINI_MODEL", "gemini-3.8-flash")
MODEL_TTS = st.secrets.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
ADMIN_PIN = st.secrets.get("ADMIN_PIN", "")

DATA_DIR = Path("du_lieu")
DATA_DIR.mkdir(exist_ok=True)
DOCS_FILE = DATA_DIR / "tai_lieu.json"

MAX_CHARS_PER_DOC = 30_000
MAX_CHARS_CONTEXT = 60_000
MAX_HISTORY = 12  # số tin nhắn gần nhất gửi kèm cho AI

# ==========================================
# 2. KHO TÀI LIỆU DÙNG CHUNG (mọi phiên đều thấy)
# ==========================================


@st.cache_resource
def get_store():
    docs = []
    if DOCS_FILE.exists():
        try:
            docs = json.loads(DOCS_FILE.read_text(encoding="utf-8"))
        except Exception:
            docs = []
    return {"lock": threading.Lock(), "docs": docs}


def save_store(store):
    try:
        DOCS_FILE.write_text(
            json.dumps(store["docs"], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
    except Exception:
        pass  # Streamlit Cloud có thể không cho ghi; dữ liệu vẫn nằm trong bộ nhớ


def extract_text(uploaded):
    name = uploaded.name.lower()
    data = uploaded.getvalue()
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if name.endswith(".docx"):
        from docx import Document

        d = Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    return ""


@st.cache_data
def read_base_material():
    try:
        return Path("tai_lieu_on_thi.txt").read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def build_context(selected_ids):
    store = get_store()
    parts, total = [], 0
    base = read_base_material()
    if base:
        parts.append(f"[Tài liệu ôn thi gốc]\n{base[:MAX_CHARS_PER_DOC]}")
        total += len(parts[0])
    for d in store["docs"]:
        if d["trang_thai"] != "Đã phê duyệt" or d["id"] not in selected_ids:
            continue
        chunk = f"[{d['ten']}]\n{d['noi_dung'][:MAX_CHARS_PER_DOC]}"
        if total + len(chunk) > MAX_CHARS_CONTEXT:
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n\n".join(parts)


# ==========================================
# 3. CHẾ ĐỘ HỌC VÀ HƯỚNG DẪN HỆ THỐNG
# ==========================================

BASE_RULES = """
Bạn là E-HERO AI, trợ lý học tiếng Anh cho học sinh THPT Việt Nam.
- Giọng điệu thân thiện, động viên, đúng tinh thần sư phạm.
- Nếu câu hỏi không liên quan đến tiếng Anh hoặc giáo dục, lịch sự từ chối bằng tiếng Việt.
- Khi có TÀI LIỆU THAM KHẢO bên dưới, ưu tiên dựa vào đó và nói rõ khi bạn dùng nó.
  Nếu tài liệu không có thông tin, trả lời bằng kiến thức chung và nói rõ điều đó.
"""

MODES = {
    "Hỏi đáp kiến thức": (
        "Giải thích bằng tiếng Việt, giữ ví dụ tiếng Anh. "
        "Từ vựng: nghĩa, từ loại, một ví dụ. Ngữ pháp: công thức, cách dùng, một ví dụ. "
        "Mặc định 80-150 từ; câu đơn giản chỉ 30-60 từ. Chỉ mở rộng khi được yêu cầu."
    ),
    "Luyện nói với Alex": (
        "Bạn đóng vai Alex, một người bạn bản xứ thân thiện. Chỉ nói TIẾNG ANH, "
        "mỗi lượt 2-3 câu ngắn, kết thúc bằng một câu hỏi để học sinh nói tiếp. "
        "Nếu học sinh mắc lỗi ngữ pháp hoặc từ vựng, sửa nhẹ nhàng ở cuối bằng một dòng "
        "bắt đầu bằng 'Tip:' (viết bằng tiếng Việt, tối đa 1 lỗi mỗi lượt)."
    ),
    "Thi nói IELTS": (
        "Bạn là giám khảo IELTS Speaking. Hỏi lần lượt từng câu (Part 1, 2, 3), "
        "bằng tiếng Anh, không giải thích dài. Sau khi học sinh trả lời, nhận xét ngắn "
        "bằng tiếng Việt theo 4 tiêu chí (Fluency, Vocabulary, Grammar, Pronunciation), "
        "gợi ý ước lượng band, rồi hỏi câu tiếp theo bằng tiếng Anh."
    ),
    "Luyện viết VSTEP/THPT": (
        "Học sinh sẽ gửi bài viết. Chấm theo bố cục, nội dung, từ vựng, ngữ pháp. "
        "Liệt kê tối đa 5 lỗi quan trọng nhất kèm bản sửa, rồi viết lại một đoạn mẫu. "
        "Nhận xét bằng tiếng Việt."
    ),
}

SPEAKING_MODES = {"Luyện nói với Alex", "Thi nói IELTS"}


def build_system_prompt(mode, level, selected_ids):
    prompt = (
        BASE_RULES
        + f"\nCHẾ ĐỘ: {mode}\n{MODES[mode]}\n"
        + f"\nTRÌNH ĐỘ HỌC SINH: {level}. Chọn từ vựng và độ dài câu phù hợp trình độ này.\n"
    )
    ctx = build_context(selected_ids)
    if ctx:
        prompt += "\n=== TÀI LIỆU THAM KHẢO ===\n" + ctx
    return prompt


# ==========================================
# 4. GỌI AI: VĂN BẢN, GIỌNG NÓI, ĐỌC TO
# ==========================================


class VoiceTurn(BaseModel):
    transcript: str
    reply: str


def history_contents():
    msgs = st.session_state.messages[-MAX_HISTORY:]
    return [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part.from_text(text=m["content"])],
        )
        for m in msgs
    ]


def with_retry(fn):
    for attempt in range(3):
        try:
            return fn()
        except APIError as e:
            code = getattr(e, "code", None)
            if code in (503, 500) and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            if code == 429:
                raise RuntimeError("API đã đạt giới hạn sử dụng. Hãy thử lại sau ít phút.")
            raise RuntimeError(f"Gemini API gặp lỗi: {e}")


def ask_text(system_prompt, history, user_text):
    contents = history + [
        types.Content(role="user", parts=[types.Part.from_text(text=user_text)])
    ]
    cfg = types.GenerateContentConfig(
        system_instruction=system_prompt, max_output_tokens=1500, temperature=0.5
    )

    def stream():
        for chunk in client.models.generate_content_stream(
            model=MODEL_CHAT, contents=contents, config=cfg
        ):
            if chunk.text:
                yield chunk.text

    return stream


def ask_voice(system_prompt, history, audio_bytes, mime):
    contents = history + [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime),
                types.Part.from_text(
                    text=(
                        "Đây là lời nói của học sinh. Hãy chép lại chính xác những gì "
                        "học sinh nói vào trường transcript (giữ nguyên lỗi nếu có), "
                        "rồi trả lời theo đúng chế độ vào trường reply."
                    )
                ),
            ],
        )
    ]
    cfg = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=1500,
        temperature=0.5,
        response_mime_type="application/json",
        response_schema=VoiceTurn,
    )

    def call():
        return client.models.generate_content(
            model=MODEL_CHAT, contents=contents, config=cfg
        )

    resp = with_retry(call)
    parsed = getattr(resp, "parsed", None)
    if parsed is None:
        parsed = VoiceTurn(**json.loads(resp.text))
    return parsed


def clean_for_speech(text):
    text = re.sub(r"[*_`#>]+", "", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    return text.strip()[:1200]


def text_to_wav(text, voice="Kore"):
    """Đọc to bằng Gemini TTS. Trả về bytes WAV hoặc None nếu lỗi."""
    try:
        resp = client.models.generate_content(
            model=MODEL_TTS,
            contents=clean_for_speech(text),
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                ),
            ),
        )
        pcm = resp.candidates[0].content.parts[0].inline_data.data
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(pcm)
        return buf.getvalue()
    except Exception:
        return None


# ==========================================
# 5. TRẠNG THÁI PHIÊN
# ==========================================

st.session_state.setdefault("messages", [])
st.session_state.setdefault("pending_text", None)
st.session_state.setdefault("goi_y", "")

# ==========================================
# 6. GIAO DIỆN
# ==========================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;800&display=swap');

:root {
  --ink: #14213d;
  --paper: #f6f8fb;
  --mark: #ffd23f;
  --voice: #0f766e;
  --line: #d9e0ea;
}
html, body, [class*="css"], .stApp { font-family: 'Be Vietnam Pro', system-ui, sans-serif; }
.stApp { background: var(--paper); color: var(--ink); }

.hero {
  display: flex; align-items: center; justify-content: space-between; gap: 24px;
  padding: 26px 30px; margin-bottom: 18px;
  background: var(--ink); color: #fff; border-radius: 20px;
}
.hero h1 { margin: 0; font-size: 2rem; font-weight: 800; line-height: 1.15; }
.hero h1 span { background: var(--mark); color: var(--ink); padding: 0 .3em; border-radius: 6px; }
.hero p { margin: 8px 0 0; color: #c9d3e6; max-width: 46ch; }
.wave { display: flex; align-items: center; gap: 5px; height: 56px; }
.wave i { display: block; width: 6px; border-radius: 3px; background: var(--mark); }
.wave i:nth-child(1){height:18px} .wave i:nth-child(2){height:36px}
.wave i:nth-child(3){height:52px} .wave i:nth-child(4){height:30px}
.wave i:nth-child(5){height:44px} .wave i:nth-child(6){height:22px}
.wave i:nth-child(7){height:34px}

.doc-row {
  background: #fff; border: 1px solid var(--line); border-left: 5px solid var(--voice);
  border-radius: 10px; padding: 12px 16px; margin-bottom: 10px;
}
.doc-row.wait { border-left-color: var(--mark); }
.doc-row b { color: var(--ink); }
.doc-row small { color: #5b6b85; }

[data-testid="stChatMessage"] { background: #fff; border: 1px solid var(--line); border-radius: 14px; }
.stButton > button { border-radius: 10px; font-weight: 600; }
@media (max-width: 700px) { .hero { flex-direction: column; align-items: flex-start; } }
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### E-HERO AI")
    page = st.radio(
        "Trang",
        ["Trò chuyện", "Kho tài liệu", "Kiểm duyệt"],
        label_visibility="collapsed",
    )

    if page == "Trò chuyện":
        st.markdown("---")
        mode = st.selectbox("Chế độ học", list(MODES.keys()))
        level = st.select_slider(
            "Trình độ", ["A2", "B1", "B2", "C1"], value="B1"
        )
        speak_back = st.toggle(
            "AI đọc to câu trả lời",
            value=mode in SPEAKING_MODES,
            help="Dùng giọng đọc của Gemini. Có thể làm chậm phản hồi vài giây.",
        )
        voice_name = st.selectbox("Giọng đọc", ["Kore", "Puck", "Charon", "Aoede"])

        approved = [
            d for d in get_store()["docs"] if d["trang_thai"] == "Đã phê duyệt"
        ]
        selected_ids = set()
        if approved:
            chosen = st.multiselect(
                "Tài liệu AI được tham khảo",
                options=[d["id"] for d in approved],
                default=[d["id"] for d in approved],
                format_func=lambda i: next(d["ten"] for d in approved if d["id"] == i),
            )
            selected_ids = set(chosen)

        if st.button("Xóa hội thoại", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# ==========================================
# TRANG 1: TRÒ CHUYỆN
# ==========================================

if page == "Trò chuyện":
    st.markdown(
        """
        <div class="hero">
          <div>
            <h1>Nói tiếng Anh với <span>Alex</span></h1>
            <p>Bấm micro bên dưới và nói. AI nghe, chép lại lời bạn, sửa lỗi
               và trả lời bằng giọng nói.</p>
          </div>
          <div class="wave"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Chủ đề gợi ý")
    cols = st.columns(4)
    suggestions = [
        ("Đảo ngữ THPT", "Giải thích cấu trúc đảo ngữ hay gặp trong đề THPT và cho 3 câu bài tập."),
        ("IELTS Writing 2", "Hướng dẫn cách viết IELTS Writing Task 2 cho người mới bắt đầu."),
        ("Nói về môi trường", "Hello Alex! Let's talk about environmental protection."),
        ("Thư phàn nàn VSTEP", "Hướng dẫn cấu trúc viết thư phàn nàn trong VSTEP kèm ví dụ."),
    ]
    for col, (label, prompt) in zip(cols, suggestions):
        if col.button(label, use_container_width=True):
            st.session_state.pending_text = prompt
            st.rerun()

    # Lịch sử hội thoại
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("audio"):
                st.audio(m["audio"], format="audio/wav")

    chat_input = st.chat_input(
        "Gõ câu hỏi hoặc bấm micro để nói...", accept_audio=True
    )

    user_text, audio_bytes, audio_mime = st.session_state.pending_text, None, "audio/wav"
    st.session_state.pending_text = None

    if chat_input:
        if isinstance(chat_input, str):
            user_text = chat_input
        else:
            get = (
                chat_input.get
                if isinstance(chat_input, dict)
                else lambda k, d=None: getattr(chat_input, k, d)
            )
            audio = get("audio", None)
            text = get("text", None)
            if audio is not None:
                audio_bytes = (
                    audio.getvalue() if hasattr(audio, "getvalue") else audio.read()
                )
                audio_mime = getattr(audio, "type", None) or "audio/wav"
            elif text:
                user_text = text

    if user_text or audio_bytes:
        system_prompt = build_system_prompt(mode, level, selected_ids)
        history = history_contents()
        reply_text, error = "", None

        if audio_bytes:
            with st.chat_message("user"):
                st.audio(audio_bytes, format=audio_mime)
                st.caption("Đang nhận dạng giọng nói...")
            try:
                with st.spinner("E-HERO AI đang nghe và suy nghĩ..."):
                    turn = ask_voice(system_prompt, history, audio_bytes, audio_mime)
                st.session_state.messages.append(
                    {"role": "user", "content": f"🎙️ {turn.transcript}"}
                )
                reply_text = turn.reply
                with st.chat_message("assistant"):
                    st.markdown(reply_text)
            except Exception as e:
                error = str(e)
        else:
            st.session_state.messages.append({"role": "user", "content": user_text})
            with st.chat_message("user"):
                st.markdown(user_text)
            with st.chat_message("assistant"):
                try:
                    reply_text = st.write_stream(
                        ask_text(system_prompt, history, user_text)
                    )
                except APIError as e:
                    error = (
                        "API đã đạt giới hạn sử dụng. Hãy thử lại sau ít phút."
                        if getattr(e, "code", None) == 429
                        else f"Gemini API gặp lỗi: {e}"
                    )
                except Exception as e:
                    error = f"Không thể xử lý yêu cầu: {e}"

        if error:
            st.error(error)
        elif reply_text:
            wav = None
            if speak_back:
                with st.spinner("Đang tạo giọng đọc..."):
                    wav = text_to_wav(reply_text, voice_name)
                if wav:
                    try:
                        st.audio(wav, format="audio/wav", autoplay=True)
                    except TypeError:
                        st.audio(wav, format="audio/wav")
                else:
                    st.caption("Không tạo được giọng đọc, bạn vẫn có thể đọc văn bản ở trên.")
            # Chỉ giữ âm thanh của câu trả lời mới nhất để tiết kiệm bộ nhớ
            for m in st.session_state.messages:
                m.pop("audio", None)
            st.session_state.messages.append(
                {"role": "assistant", "content": reply_text, "audio": wav}
            )

# ==========================================
# TRANG 2: KHO TÀI LIỆU
# ==========================================

elif page == "Kho tài liệu":
    st.markdown("## Kho tài liệu tiếng Anh")
    st.write(
        "Tài liệu được thầy cô duyệt sẽ trở thành nguồn tham khảo cho AI "
        "khi trả lời trong mục Trò chuyện."
    )

    store = get_store()

    with st.expander("Đóng góp tài liệu mới", expanded=True):
        author = st.text_input("Tên người đóng góp")
        files = st.file_uploader(
            "Chọn file PDF, DOCX hoặc TXT",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
        )
        if st.button("Gửi để kiểm duyệt"):
            if not author.strip() or not files:
                st.warning("Hãy nhập tên và chọn ít nhất một file.")
            else:
                ok = 0
                for f in files:
                    try:
                        text = extract_text(f).strip()
                    except Exception as e:
                        st.error(f"Không đọc được {f.name}: {e}")
                        continue
                    if not text:
                        st.warning(
                            f"{f.name} không có văn bản đọc được "
                            "(file scan hoặc ảnh chưa được hỗ trợ)."
                        )
                        continue
                    with store["lock"]:
                        store["docs"].append(
                            {
                                "id": uuid.uuid4().hex[:10],
                                "ten": f.name,
                                "nguoi_gui": author.strip(),
                                "trang_thai": "Chờ phê duyệt",
                                "ngay": datetime.now().strftime("%d/%m/%Y"),
                                "noi_dung": text[:MAX_CHARS_PER_DOC],
                            }
                        )
                        save_store(store)
                    ok += 1
                if ok:
                    st.success(f"Đã gửi {ok} tài liệu vào danh sách chờ duyệt.")

    st.markdown("### Tài liệu đã duyệt")
    approved = [d for d in store["docs"] if d["trang_thai"] == "Đã phê duyệt"]
    if not approved:
        st.info("Chưa có tài liệu nào được duyệt. Hãy là người đóng góp đầu tiên.")
    for d in approved:
        st.markdown(
            f"""<div class="doc-row"><b>{html.escape(d['ten'])}</b><br>
            <small>Người gửi: {html.escape(d['nguoi_gui'])} · {html.escape(d.get('ngay', ''))}
            · {len(d['noi_dung']):,} ký tự</small></div>""",
            unsafe_allow_html=True,
        )

# ==========================================
# TRANG 3: KIỂM DUYỆT
# ==========================================

else:
    st.markdown("## Kiểm duyệt tài liệu")

    if not ADMIN_PIN:
        st.error("Chưa đặt ADMIN_PIN trong Secrets nên trang này đang bị khóa.")
        st.stop()

    pin = st.text_input("Mã PIN quản trị", type="password")
    if pin and not hmac.compare_digest(
        hashlib.sha256(pin.encode()).digest(),
        hashlib.sha256(str(ADMIN_PIN).encode()).digest(),
    ):
        st.error("Mã PIN không đúng.")
    elif pin:
        store = get_store()
        waiting = [d for d in store["docs"] if d["trang_thai"] == "Chờ phê duyệt"]
        st.markdown(f"### Chờ duyệt ({len(waiting)})")
        if not waiting:
            st.info("Không có tài liệu nào đang chờ.")
        for d in waiting:
            st.markdown(
                f"""<div class="doc-row wait"><b>{html.escape(d['ten'])}</b><br>
                <small>Người gửi: {html.escape(d['nguoi_gui'])}
                · {len(d['noi_dung']):,} ký tự</small></div>""",
                unsafe_allow_html=True,
            )
            with st.expander("Xem trước nội dung"):
                st.text(d["noi_dung"][:1500])
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("Duyệt", key=f"ok_{d['id']}"):
                with store["lock"]:
                    d["trang_thai"] = "Đã phê duyệt"
                    save_store(store)
                st.rerun()
            if c2.button("Từ chối", key=f"no_{d['id']}"):
                with store["lock"]:
                    store["docs"] = [x for x in store["docs"] if x["id"] != d["id"]]
                    save_store(store)
                st.rerun()
