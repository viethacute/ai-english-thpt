
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError
import time

# ==========================================
# 1. CẤU HÌNH TRANG VÀ API
# ==========================================

st.set_page_config(
    page_title="E-HERO AI Platform",
    page_icon="🤖",
    layout="wide",
)

if "GEMINI_API_KEY" not in st.secrets:
    st.error(
        "Chưa cấu hình GEMINI_API_KEY. "
        "Hãy thêm API Key trong mục Secrets của Streamlit Cloud."
    )
    st.stop()

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

# ==========================================
# 2. HƯỚNG DẪN HỆ THỐNG
# ==========================================

huong_dan_he_thong = """
Bạn là E-HERO AI, trợ lý học tiếng Anh dành cho học sinh THPT.

QUY TẮC:
- Trả lời ngắn gọn, rõ ràng, đúng trọng tâm.
- Giải thích bằng tiếng Việt; giữ ví dụ tiếng Anh khi cần.
- Từ vựng: nêu nghĩa, từ loại và một ví dụ.
- Ngữ pháp: nêu công thức, cách dùng và một ví dụ.
- IELTS/VSTEP: hướng dẫn thực tế, phù hợp trình độ học sinh.
- Bài tập: giải thích các bước chính.
- Mặc định khoảng 80–150 từ; câu hỏi đơn giản
  trả lời trong 30–60 từ.
- Chỉ mở rộng khi học sinh yêu cầu.
- Nếu câu hỏi không liên quan đến tiếng Anh hoặc
  giáo dục, lịch sự từ chối bằng tiếng Việt.
- Giọng điệu thân thiện, sư phạm, động viên.
"""

try:
    with open("tai_lieu_on_thi.txt", "r", encoding="utf-8") as f:
        noi_dung_tai_lieu = f.read()
except FileNotFoundError:
    noi_dung_tai_lieu = ""

huong_dan_day_du = (
    huong_dan_he_thong
    + "\n\n=== TÀI LIỆU ÔN THI ===\n"
    + noi_dung_tai_lieu
)

# ==========================================
# 3. KHỞI TẠO DỮ LIỆU
# ==========================================

if "kho_tai_lieu" not in st.session_state:
    st.session_state.kho_tai_lieu = [
        {
            "ten": "Đề thi thử THPT Quốc gia 2026.pdf",
            "nguoi_gui": "Thầy Minh (GV Tiếng Anh)",
            "trang_thai": "Đã phê duyệt",
        },
        {
            "ten": "Bộ từ vựng IELTS chuyên sâu 8.0.pdf",
            "nguoi_gui": "Bạn An (Lớp 12A1)",
            "trang_thai": "Đã phê duyệt",
        },
    ]

if "danh_sach_cho" not in st.session_state:
    st.session_state.danh_sach_cho = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "goi_y_prompt" not in st.session_state:
    st.session_state.goi_y_prompt = ""

# ==========================================
# 4. GIAO DIỆN CHUNG
# ==========================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            135deg, #f8fafc 0%, #f1f5f9 100%
        );
    }

    .main-title {
        background: linear-gradient(45deg, #1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: sans-serif;
        font-weight: 800;
        text-align: center;
    }

    .card-luxury {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        border-top: 4px solid #2563eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("## 🧭 BẢNG ĐIỀU HƯỚNG")

trang_hien_tai = st.sidebar.radio(
    "Chọn không gian làm việc:",
    [
        "🤖 Trợ lý AI Thông Minh",
        "📚 Kho Tài Liệu Học Tập",
        "🔐 Cổng Kiểm Duyệt Admin",
    ],
)

# ==========================================
# TRANG 1: TRỢ LÝ AI
# ==========================================

if trang_hien_tai == "🤖 Trợ lý AI Thông Minh":

    st.markdown(
        "<h1 class='main-title'>🤖 PROJECT E-HERO AI ECOSYSTEM</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='text-align:center;color:#64748b;'>"
        "Trợ lý học tiếng Anh - Không gian học tập toàn diện"
        "</p>",
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown(
            """
            <div class='card-luxury'>
                <h4 style='color:#1e293b;'>
                    💡 GỢI Ý NỘI DUNG HỌC TẬP
                </h4>
                <p style='color:#475569;'>
                    Chọn một chủ đề để tạo câu hỏi mẫu.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📌 THPT Quốc Gia"):
                st.session_state.goi_y_prompt = (
                    "Giải thích cấu trúc câu đảo ngữ "
                    "thường gặp trong đề thi THPT và cho bài tập."
                )

        with col2:
            if st.button("👑 IELTS Writing"):
                st.session_state.goi_y_prompt = (
                    "Hướng dẫn cách viết IELTS Writing Task 2 "
                    "cho người mới bắt đầu."
                )

        with col3:
            if st.button("🗣️ Speaking với Alex"):
                st.session_state.goi_y_prompt = (
                    "Hello Alex! Let's practice speaking English. "
                    "Can we chat about environmental protection?"
                )

        with col4:
            if st.button("📝 VSTEP"):
                st.session_state.goi_y_prompt = (
                    "Hướng dẫn cấu trúc viết thư phàn nàn "
                    "trong kỳ thi VSTEP và cho ví dụ."
                )

    if st.session_state.goi_y_prompt:
        st.info(
            "📋 Câu hỏi mẫu: "
            + st.session_state.goi_y_prompt
        )
        if st.button("Dùng câu hỏi mẫu"):
            st.session_state.messages.append({
                "role": "user",
                "content": st.session_state.goi_y_prompt,
            })
            st.session_state.goi_y_prompt = ""
            st.rerun()

    # Hiển thị lịch sử hội thoại
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Ô nhập liệu
    chat_input_data = st.chat_input(
        "Nhập câu hỏi hoặc gửi giọng nói...",
        accept_audio=True,
    )

    # Xử lý tin nhắn mới
    if chat_input_data:

        user_display_message = ""
        ai_content_input = None

        audio_file = getattr(chat_input_data, "audio", None)
        text_input = getattr(chat_input_data, "text", None)

        if audio_file is not None:
            user_display_message = (
                "🎙️ Học sinh đã gửi một đoạn ghi âm."
            )

            try:
                if hasattr(audio_file, "getvalue"):
                    audio_bytes = audio_file.getvalue()
                else:
                    audio_bytes = audio_file.read()

                mime_type = (
                    getattr(audio_file, "type", None)
                    or "audio/wav"
                )

                ai_content_input = [
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=mime_type,
                    ),
                    (
                        "Hãy phân tích nội dung lời nói trong "
                        "bản ghi âm và phản hồi bằng văn bản."
                    ),
                ]

            except Exception as e:
                st.error(f"Không thể đọc file âm thanh: {e}")

        elif text_input:
            user_display_message = text_input
            ai_content_input = text_input

        if ai_content_input is not None:

            st.session_state.messages.append({
                "role": "user",
                "content": user_display_message,
            })

            with st.chat_message("user"):
                st.markdown(user_display_message)

            # Toàn bộ xử lý AI nằm trong khối chat của trang 1
            with st.chat_message("assistant"):

                placeholder = st.empty()
                placeholder.markdown("*E-HERO AI đang xử lý...*")

                response = None

                for attempt in range(3):
                    try:
                        start_time = time.perf_counter()

                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=ai_content_input,
                            config=types.GenerateContentConfig(
                                system_instruction=huong_dan_day_du,
                                max_output_tokens=450,
                                temperature=0.5,
                            ),
                        )

                        elapsed = time.perf_counter() - start_time

                        st.caption(
                            f"⏱️ Thời gian xử lý: {elapsed:.2f} giây"
                        )
                        break

                    except APIError as e:
                        status = getattr(e, "code", None)

                        if status == 503 and attempt < 2:
                            time.sleep(2 ** (attempt + 1))
                            continue

                        if status == 429:
                            st.error(
                                "API đã đạt giới hạn sử dụng. "
                                "Hãy kiểm tra quota Gemini."
                            )
                        else:
                            st.error(f"Gemini API gặp lỗi: {e}")

                        break

                    except Exception as e:
                        st.error(f"Không thể xử lý yêu cầu: {e}")
                        break

                if response is not None:
                    full_text_response = (
                        response.text
                        or "AI chưa tạo được câu trả lời."
                    )

                    placeholder.markdown(full_text_response)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_text_response,
                    })

# ==========================================
# TRANG 2: KHO TÀI LIỆU HỌC TẬP
# ==========================================

elif trang_hien_tai == "📚 Kho Tài Liệu Học Tập":

    st.markdown(
        "<h1 style='color:#1e3a8a;'>"
        "📚 KHO TRI THỨC VÀ TÀI LIỆU TIẾNG ANH"
        "</h1>",
        unsafe_allow_html=True,
    )

    st.write(
        "Nơi học sinh và thầy cô đóng góp tài liệu học tập."
    )

    with st.expander(
        "📤 ĐÓNG GÓP TÀI LIỆU MỚI",
        expanded=True,
    ):
        ten_nguoi_gui = st.text_input(
            "Tên người đóng góp / Tác giả:"
        )

        file_upload = st.file_uploader(
            "Chọn file PDF, DOCX hoặc TXT:",
            type=["pdf", "docx", "txt"],
        )

        if st.button("Gửi tài liệu để kiểm duyệt 🚀"):

            if ten_nguoi_gui.strip() and file_upload is not None:

                st.session_state.danh_sach_cho.append({
                    "ten": file_upload.name,
                    "nguoi_gui": ten_nguoi_gui.strip(),
                    "trang_thai": "Chờ phê duyệt",
                })

                st.success(
                    "Đã gửi tài liệu vào danh sách chờ duyệt."
                )

            else:
                st.warning(
                    "Vui lòng nhập tên và chọn file tài liệu."
                )

    st.markdown("### 📥 DANH MỤC TÀI LIỆU")

    if not st.session_state.kho_tai_lieu:
        st.info("Chưa có tài liệu nào.")

    for doc in st.session_state.kho_tai_lieu:
        st.markdown(
            f"""
            <div style='background:white;padding:15px;
                        border-radius:10px;margin-bottom:10px;'>
                <b style='color:#1e3a8a;'>
                    📄 {doc['ten']}
                </b>
                <br>
                <small>
                    Người gửi: {doc['nguoi_gui']}
                    | Trạng thái: {doc['trang_thai']}
                </small>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==========================================
# TRANG 3: CỔNG KIỂM DUYỆT ADMIN
# ==========================================

elif trang_hien_tai == "🔐 Cổng Kiểm Duyệt Admin":

    st.markdown(
        "<h1 style='color:#1e3a8a;'>"
        "🔐 CỔNG KIỂM DUYỆT ADMIN"
        "</h1>",
        unsafe_allow_html=True,
    )

    ma_pin = st.text_input(
        "Nhập mã PIN Admin:",
        type="password",
    )

    # PIN này chỉ để trình diễn; không đủ an toàn cho môi trường thật.
    if ma_pin == "0601":

        st.success("Đã mở giao diện kiểm duyệt.")

        st.markdown("### 📥 DANH SÁCH CHỜ DUYỆT")

        if not st.session_state.danh_sach_cho:
            st.info("Không có tài liệu chờ duyệt.")

        else:
            for i, doc in enumerate(
                list(st.session_state.danh_sach_cho)
            ):
                st.write(
                    f"📁 **{doc['ten']}** — "
                    f"Người gửi: {doc['nguoi_gui']}"
                )

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    if st.button(
                        f"✅ Duyệt file {i + 1}",
                        key=f"duyet_{i}",
                    ):
                        item = st.session_state.danh_sach_cho.pop(i)
                        item["trang_thai"] = "Đã phê duyệt"
                        st.session_state.kho_tai_lieu.append(item)
                        st.rerun()

                with col_btn2:
                    if st.button(
                        f"❌ Từ chối file {i + 1}",
                        key=f"tu_choi_{i}",
                    ):
                        st.session_state.danh_sach_cho.pop(i)
                        st.rerun()

                st.markdown("---")

    elif ma_pin:
        st.error("Mã PIN không chính xác.")
