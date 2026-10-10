import streamlit as st
from google import genai
from google.genai import types
import time

# 1. CẤU HÌNH TRUY XUẤT CHÌA KHÓA AI BẢO MẬT
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Chưa cấu hình API Key trong mục Secrets của hệ thống máy chủ.")

# 2. KHỞI TẠO BỘ NHỚ LƯU TRỮ TÀI LIỆU TẠM THỜI (Hệ thống phê duyệt)
if "kho_tai_lieu" not in st.session_state:
    st.session_state.kho_tai_lieu = [
        {"ten": "Đề thi thử THPT Quốc gia 2026 - Đột phá Ngữ pháp.pdf", "nguoi_gui": "Thầy Minh (GV Tiếng Anh)", "trang_thai": "Đã phê duyệt", "link": "#"},
        {"ten": "Bộ từ vựng IELTS Chuyên sâu - Nâng band Thần tốc 8.0.pdf", "nguoi_gui": "Bạn An (Lớp 12A1)", "trang_thai": "Đã phê duyệt", "link": "#"}
    ]
if "danh_sach_cho" not in st.session_state:
    st.session_state.danh_sach_cho = []

# Đọc tài liệu huấn luyện bổ sung từ file text
try:
    with open("tai_lieu_on_thi.txt", "r", encoding="utf-8") as f:
        du_lieu_huan_luyen = f.read()
except FileNotFoundError:
    du_lieu_huan_luyen = "Hệ thống đang sử dụng cơ sở dữ liệu mặc định."

prompt_he_thong = (
    "Bạn là Hệ sinh thái Trợ lý AI Tiếng Anh toàn diện dành cho học sinh THPT.\n"
    "Dưới đây là tài liệu chuyên sâu do nhóm tác giả nghiên cứu nạp vào để HUẤN LUYỆN bạn:\n"
    f"=== DỮ LIỆU HUẤN LUYỆN ===\n{du_lieu_huan_luyen}\n========================\n"
    "Học sinh có thể hỏi bạn bất cứ điều gì liên quan đến từ khóa tiếng Anh (THPT, IELTS, VSTEP, Từ vựng, Ngữ pháp, bài tập...).\n"
    "Nếu câu hỏi KHÔNG LIÊN QUAN đến Tiếng Anh hoặc Giáo dục, hãy lịch sự từ chối bằng tiếng Việt.\n"
    "Luôn trả lời bằng tiếng Việt khi giải thích ngữ pháp, ngôn ngữ thân thiện, sư phạm và động viên học sinh."
)

# 3. THIẾT KẾ GIAO DIỆN CHÂN THỰC VÀ THANH ĐIỀU HƯỚNG TRANG (MULTIPAGE)
st.set_page_config(page_title="E-HERO AI Platform", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); }
    .main-title { background: linear-gradient(45deg, #1e3a8a, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-family: 'Inter', sans-serif; font-weight: 800; text-align: center; }
    .card-luxury { background-color: #ffffff; padding: 20px; border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.03); margin-bottom: 20px; border-top: 4px solid #2563eb; }
    .keyword-badge { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 20px; padding: 5px 15px; font-size: 0.85em; font-weight: 600; color: #334155; text-align: center; display: inline-block; margin: 4px; cursor: pointer; }
    </style>
""", unsafe_allow_html=True)

# Thanh Menu dọc điều hướng giữa các trang
st.sidebar.markdown("## 🧭 BẢNG ĐIỀU HƯỚNG")
trang_hien_tai = st.sidebar.radio("Chọn không gian làm việc:", ["🤖 Trợ lý AI Thông Minh", "📚 Kho Tài Liệu Học Tập", "🔐 Cổng Kiểm Duyệt Admin"])

# ==========================================
# TRANG 1: TRỢ LÝ AI CHAT THÔNG MINH
# ==========================================
if trang_hien_tai == "🤖 Trợ lý AI Thông Minh":
    st.markdown("<h1 class='main-title'>🤖 PROJECT E-HERO AI ECOSYSTEM</h1>", unsafe_allow_html=True)
    st.caption("<p style='text-align: center; color: #64748b;'>Hệ thống Trợ lý ảo Cá nhân hóa - Không gian học tập Tiếng Anh toàn diện</p>", unsafe_allow_html=True)
    
    # Khu vực đưa ra hướng dẫn gợi ý từ khóa thông minh cho học sinh
    with st.container():
        st.markdown("""
        <div class='card-luxury'>
        <h4 style='color: #1e293b; margin-top:0; margin-bottom:8px;'>💡 HƯỚNG DẪN GỢI Ý NỘI DUNG HỎI THEO TỪ KHÓA:</h4>
        <p style='color: #475569; font-size:0.9em; margin-bottom:12px;'>Bạn có thể đặt bất kỳ câu hỏi nào liên quan đến các chủ đề Tiếng Anh dưới đây. Nhấp vào từ khóa để xem câu hỏi mẫu gợi ý:</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tạo các nút bấm đóng vai trò là "Từ khóa gợi ý" trực quan cho học sinh
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📌 Từ khóa: THPT Quốc Gia"):
                st.session_state.goi_y_prompt = "Hãy giải thích chi tiết cấu trúc câu Đảo ngữ (Inversion) thường gặp trong đề thi THPT và cho ví dụ minh họa kèm bài tập."
        with col2:
            if st.button("👑 Từ khóa: IELTS Writing"):
                st.session_state.goi_y_prompt = "Chấm điểm và sửa bài luận sau theo 4 tiêu chí chuẩn Rubric IELTS: [Dán bài văn của bạn vào đây]"
        with col3:
            if st.button("🗣️ Từ khóa: Alex Speaking"):
                st.session_state.goi_y_prompt = "Hello Alex! Let's practice speaking english. Can we chat about environmental protection?"
        with col4:
            if st.button("📝 Từ khóa: Chứng chỉ VSTEP"):
                st.session_state.goi_y_prompt = "Hướng dẫn mình cấu trúc viết thư phàn nàn (Letter of Complaint) để đạt điểm cao trong kỳ thi VSTEP."

    # Tạo ô text hiển thị câu hỏi mẫu sau khi học sinh click từ khóa
    if "goi_y_prompt" in st.session_state and st.session_state.goi_y_prompt:
        st.info(f"📋 **Câu hỏi gợi ý mẫu vừa nạp:** {st.session_state.goi_y_prompt}")
        st.caption("Mẹo: Bạn có thể copy câu trên dán vào ô chat dưới cùng để gửi cho AI xử lý nhanh!")

    # Cấu trúc phòng chat Bong bóng Messenger
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    chat_input_data = st.chat_input(placeholder="Hỏi bất cứ điều gì về THPT, IELTS, VSTEP, Từ vựng, Ngữ pháp...", accept_audio=True)

    if chat_input_data:
        user_display_message = ""
        ai_content_input = None

        is_audio_file = hasattr(chat_input_data, 'audio') and chat_input_data.audio is not None

        if is_audio_file:
            user_display_message = "🎙️ *[Học sinh vừa gửi một đoạn ghi âm giọng nói]*"
            try:
                audio_bytes = chat_input_data.audio.read()
                ai_content_input = [
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                    "Học sinh đang luyện nói tiếng Anh giao tiếp phản xạ. Hãy nghe đoạn ghi âm trên và phản hồi."
                ]
            except:
                ai_content_input = "Hello Alex!"
        else:
            user_display_message = chat_input_data.text
            ai_content_input = user_display_message

        st.session_state.messages.append({"role": "user", "content": user_display_message})
        with st.chat_message("user"):
            st.markdown(user_display_message)

        with st.chat_message("assistant"):
            with st.spinner("E-HERO AI đang nghiên cứu dữ liệu và tư duy..."):
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=ai_content_input,
                            config=types.GenerateContentConfig(system_instruction=prompt_he_thong)
                        )
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                        break
                    except Exception as e:
                        if "503" in str(e) and attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        else:
                            st.error(f"Lỗi kết nối máy chủ AI: {str(e)}")
                            break

# ==========================================
# TRANG 2: KHO TÀI LIỆU HỌC TẬP (CHO TẢI LÊN)
# ==========================================
elif trang_hien_tai == "📚 Kho Tài Liệu Học Tập":
    st.markdown("<h1 style='color:#1e3a8a;'>📚 KHO TRI THỨC VÀ TÀI LIỆU TIẾNG ANH CHIA SẺ</h1>", unsafe_allow_html=True)
    st.write("Nơi học sinh và thầy cô chia sẻ tài liệu ôn thi chất lượng cao (Đã qua kiểm duyệt bảo mật).")
    
    # Phần 1: Form tải tài liệu lên mạng của Học sinh
    with st.expander("📤 ĐÓNG GÓP TÀI LIỆU MỚI (CẦN DUYỆT)", expanded=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            ten_nguoi_gui = st.text_input("Tên người đóng góp / Tác giả:", placeholder="Ví dụ: Nguyễn Văn A - Lớp 12A2")
        with col_f2:
            file_upload = st.file_uploader("Chọn tệp tài liệu của bạn (PDF, DOCX, TXT):", type=["pdf", "docx", "txt"])
        
        if st.button("Gửi tài liệu lên Hệ thống kiểm duyệt 🚀"):
            if ten_nguoi_gui and file_upload:
                # Lưu thông tin tạm thời vào Danh sách chờ duyệt
                st.session_state.danh_sach_cho.append({
                    "ten": file_upload.name,
                    "nguoi_gui": ten_nguoi_gui,
                    "trang_thai": "Chờ phê duyệt"
                })
                st.success("🎉 Gửi tài liệu thành công! Tài liệu đã được chuyển tới phòng kiểm duyệt của Ban quản trị nhà trường.")
            else:
                st.warning("⚠️ Vui lòng điền đầy đủ thông tin tên tác giả và chọn file tài liệu trước khi gửi.")

    # Phần 2: Hiển thị danh mục tài liệu đã được duyệt cho mọi người tải về
    st.markdown("### 📥 DANH MỤC TÀI LIỆU CHÍNH THỨC")
    for doc in st.session_state.kho_tai_lieu:
        with st.container():
            st.markdown(f"""
            <div style='background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-bottom: 10px;'>
                <b style='color:#1e3a8a; font-size:1.05em;'>📄 {doc['ten']}</b><br>
                <small style='color:#64748b;'>Đóng góp bởi: {doc['nguoi_gui']} | Trạng thái: <span style='color:green; font-weight:bold;'>{doc['trang_thai']}</span></small>
            </div>
            """, unsafe_allow_html=True)
