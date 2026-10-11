import streamlit as st
from google import genai
from google.genai import types

# 1. CẤU HÌNH TRUY XUẤT CHÌA KHÓA AI BẢO MẬT
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Chưa cấu hình API Key trong mục Secrets của hệ thống máy chủ.")

# MẸO CÔNG NGHỆ CAO: CACHE CỐ ĐỊNH FILE TÀI LIỆU VÀO RAM ĐỂ TRÁNH QUÉT LẠI NHIỀU LẦN
@st.cache_resource
def nap_kho_tri_thuc_sieu_toc():
    try:
        with open("tai_lieu_on_thi.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Hệ thống đang sử dụng cơ sở dữ liệu mặc định."

du_lieu_huan_luyen = nap_kho_tri_thuc_sieu_toc()

# 2. KHỞI TẠO BỘ NHỚ LƯU TRỮ TÀI LIỆU TẠM THỜI (Hệ thống phê duyệt)
if "kho_tai_lieu" not in st.session_state:
    st.session_state.kho_tai_lieu = [
        {"ten": "Đề thi thử THPT Quốc gia 2026 - Đột phá Ngữ pháp.pdf", "nguoi_gui": "Thầy Minh (GV Tiếng Anh)", "trang_thai": "Đã phê duyệt"},
        {"ten": "Bộ từ vựng IELTS Chuyên sâu - Nâng band Thần tốc 8.0.pdf", "nguoi_gui": "Bạn An (Lớp 12A1)", "trang_thai": "Đã phê duyệt"}
    ]
if "danh_sach_cho" not in st.session_state:
    st.session_state.danh_sach_cho = []

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
    </style>
""", unsafe_allow_html=True)

st.sidebar.markdown("## 🧭 BẢNG ĐIỀU HƯỚNG")
trang_hien_tai = st.sidebar.radio("Chọn không gian làm việc:", ["🤖 Trợ lý AI Thông Minh", "📚 Kho Tài Liệu Học Tập", "🔐 Cổng Kiểm Duyệt Admin"])

# ==========================================
# TRANG 1: TRỢ LÝ AI CHAT THÔNG MINH
# ==========================================
# CHỈNH SỬA VÀ THAY THẾ ĐOẠN XỬ LÝ CHAT Ở TRANG 1 TRONG FILE CỦA BẠN:

# THAY THẾ ĐOẠN XỬ LÝ CHAT Ở TRANG 1 TRONG FILE CỦA BẠN BẰNG ĐOẠN CODE NÀY:

if trang_hien_tai == "🤖 Trợ lý AI Thông Minh":
    st.markdown("<h1 class='main-title'>🤖 PROJECT E-HERO AI ECOSYSTEM</h1>", unsafe_allow_html=True)
    # ... (Giữ nguyên phần giao diện và các từ khóa gợi ý ban đầu của bạn) ...

    # Khởi tạo bộ nhớ chat nếu chưa có
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Hiển thị lịch sử chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Nếu tin nhắn trước đó của AI có chứa âm thanh, hiển thị lại trình phát audio
            if message["role"] == "assistant" and "audio" in message:
                st.audio(message["audio"], format="audio/mp3")

    # BẬT CHỨC NĂNG NHẬN CẢ AUDIO VÀ TEXT TỪ CHAT INPUT
    chat_input_data = st.chat_input(placeholder="Hỏi bằng chữ hoặc gửi giọng nói qua micro...", accept_audio=True)

    if chat_input_data:
        user_display_message = ""
        ai_content_input = None

        # Kiểm tra xem người dùng gửi âm thanh hay nhập chữ
        is_audio_file = hasattr(chat_input_data, 'audio') and chat_input_data.audio is not None

        if is_audio_file:
            user_display_message = "🎙️ *[Học sinh vừa gửi một đoạn ghi âm giọng nói]*"
            try:
                audio_bytes = chat_input_data.audio.read()
                # Nạp dữ liệu âm thanh dạng Byte để gửi lên Gemini 3.8
                ai_content_input = [
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                    "Học sinh đang luyện nói tiếng Anh. Hãy nghe kỹ, nhận xét ngắn gọn lỗi phát âm/ngữ pháp và phản hồi lại bằng cả văn bản và giọng nói."
                ]
            except Exception as e:
                ai_content_input = "Hello Alex!"
        else:
            user_display_message = chat_input_data.text
            ai_content_input = user_display_message

        # Lưu và hiển thị câu hỏi của User lên màn hình
        st.session_state.messages.append({"role": "user", "content": user_display_message})
        with st.chat_message("user"):
            st.markdown(user_display_message)

        # XỬ LÝ PHẢN HỒI TỪ GEMINI 3.8 FLASH (YÊU CẦU ĐẦU RA CÓ GIỌNG NÓI)
        with st.chat_message("assistant"):
            try:
                # Tạo khu vực hiển thị chữ tạm thời để tạo cảm giác phản hồi nhanh
                van_ban_placeholder = st.empty()
                van_ban_placeholder.markdown("*Đang xử lý dữ liệu và tạo giọng nói...*")
                
                # GỌI API GEMINI 3.8 FLASH CHÍNH XÁC THEO KHUYẾN NGHỊ CỦA GOOGLE
                response = client.models.generate_content(
                    model='gemini-3.8-flash', # Đã cập nhật tên mô hình chuẩn xác [1]
                    contents=ai_content_input,
                    config=types.GenerateContentConfig(
                        system_instruction=prompt_he_thong,
                        # THAM SỐ QUAN TRỌNG: Ép mô hình trả về cả văn bản TEXT và file âm thanh AUDIO
                        response_modalities=["TEXT", "AUDIO"] 
                    )
                )

                # Trích xuất văn bản trả về
                full_text_response = response.text if response.text else "Mình đã nghe và xử lý đoạn ghi âm của bạn!"
                van_ban_placeholder.markdown(full_text_response)

                # Tìm và trích xuất mảng Byte âm thanh (Audio chunks) ẩn bên trong kết quả trả về
                audio_data_bytes = None
                if response.candidates and response.candidates[0].content:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data and "audio" in part.inline_data.mime_type:
                            audio_data_bytes = part.inline_data.data
                            break

                # Nếu có dữ liệu âm thanh từ AI, xuất trình phát trên giao diện web ngay lập tức
                if audio_data_bytes:
                    st.audio(audio_data_bytes, format="audio/mp3")
                    # Lưu toàn bộ trạng thái chữ + audio vào lịch sử phiên làm việc
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": full_text_response, 
                        "audio": audio_data_bytes
                    })
                else:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": full_text_response
                    })

            except Exception as e:
                st.error(f"Lỗi kết nối máy chủ AI: {str(e)}")
# ==========================================
# TRANG 2: KHO TÀI LIỆU HỌC TẬP (CHO TẢI LÊN)
# ==========================================
elif trang_hien_tai == "📚 Kho Tài Liệu Học Tập":
    st.markdown("<h1 style='color:#1e3a8a;'>📚 KHO TRI THỨC VÀ TÀI LIỆU TIẾNG ANH CHIA SẺ</h1>", unsafe_allow_html=True)
    st.write("Nơi học sinh và thầy cô chia sẻ tài liệu ôn thi chất lượng cao (Đã qua kiểm duyệt bảo mật).")
    
    with st.expander("📤 ĐÓNG GÓP TÀI LIỆU MỚI (CẦN DUYỆT)", expanded=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            ten_nguoi_gui = st.text_input("Tên người đóng góp / Tác giả:", placeholder="Ví dụ: Nguyễn Văn A - Lớp 12A2")
        with col_f2:
            file_upload = st.file_uploader("Chọn tệp tài liệu của bạn (PDF, DOCX, TXT):", type=["pdf", "docx", "txt"])
        
        if st.button("Gửi tài liệu lên Hệ thống kiểm duyệt 🚀"):
            if ten_nguoi_gui and file_upload:
                st.session_state.danh_sach_cho.append({
                    "ten": file_upload.name,
                    "nguoi_gui": ten_nguoi_gui,
                    "trang_thai": "Chờ phê duyệt"
                })
                st.success("🎉 Gửi tài liệu thành công! Tài liệu đã được chuyển tới phòng kiểm duyệt của Ban quản trị nhà trường.")
            else:
                st.warning("⚠️ Vui lòng điền đầy đủ thông tin tên tác giả và chọn file tài liệu trước khi gửi.")

    st.markdown("### 📥 DANH MỤC TÀI LIỆU CHÍNH THỨC")
    for doc in st.session_state.kho_tai_lieu:
        st.markdown(f"""
        <div style='background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-bottom: 10px;'>
            <b style='color:#1e3a8a; font-size:1.05em;'>📄 {doc['ten']}</b><br>
            <small style='color:#64748b;'>Đóng góp bởi: {doc['nguoi_gui']} | Trạng thái: <span style='color:green; font-weight:bold;'>{doc['trang_thai']}</span></small>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TRANG 3: CỔNG KIỂM DUYỆT ADMIN (ĐA VÁ LỖI THỤT LỀ 100%)
# ==========================================
elif trang_hien_tai == "🔐 Cổng Kiểm Duyệt Admin":
    st.markdown("<h1 style='color:#1e3a8a;'>🔐 CỔNG KIỂM DUYỆT TÀI LIỆU DÀNH CHO ADMIN</h1>", unsafe_allow_html=True)
    ma_pin = st.text_input("Nhập mã PIN xác thực quyền Quản trị viên (Admin):", type="password")
    
    if ma_pin == "0601":
        st.success("🔓 Xác thực thành công! Quyền Quản trị viên đã được kích hoạt.")
        st.markdown("### 📥 DANH SÁCH TÀI LIỆU ĐANG CHỜ DUYỆT")
        
        if not st.session_state.danh_sach_cho:
            st.info("Hiện tại chưa có tài liệu nào cần phê duyệt.")
        else:
            # Tạo một mảng bản sao danh sách để vòng lặp chạy mượt mà không dính lỗi chỉ mục
            danh_sach_tam = list(st.session_state.danh_sach_cho)
            
            for i, doc in enumerate(danh_sach_tam):
                st.write(f"📁 **Tên file:** {doc['ten']} — *Người gửi:* {doc['nguoi_gui']}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(f"✅ Duyệt file {i+1}", key=f"duyet_{i}"):
                        item = st.session_state.danh_sach_cho.pop(i)
                        item["trang_thai"] = "Đã phê duyệt"
                        st.session_state.kho_tai_lieu.append(item)
                        st.rerun()
                with col_btn2:
                    if st.button(f"❌ Từ chối file {i+1}", key=f"xoa_{i}"):
                        st.session_state.danh_sach_cho.pop(i)
                        st.rerun()
                st.markdown("---")
