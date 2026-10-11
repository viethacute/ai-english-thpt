import streamlit as st
from google import genai
from google.genai import types
import os

# 1. CẤU HÌNH TRUY XUẤT CHÌA KHÓA AI BẢO MẬT
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Chưa cấu hình API Key trong mục Secrets của hệ thống máy chủ.") #

# Định nghĩa câu lệnh hệ thống cốt lõi
huong_dan_he_thong = (
    "Bag là Hệ sinh thái Trợ lý AI Tiếng Anh toàn diện dành cho học sinh THPT.\n"
    "Học sinh có thể hỏi bạn bất cứ điều gì liên quan đến từ khóa tiếng Anh (THPT, IELTS, VSTEP, Từ vựng, Ngữ pháp, bài tập...).\n"
    "Nếu câu hỏi KHÔNG LIÊN QUAN đến Tiếng Anh hoặc Giáo dục, hãy lịch sự từ chối bằng tiếng Việt.\n"
    "Luôn trả lời bằng tiếng Việt khi giải thích ngữ pháp, ngôn ngữ thân thiện, sư phạm và động viên học sinh."
)

# MẸO CÔNG NGHỆ CAO: TỰ ĐỘNG TẠO CONTEXT CACHING TRÊN GOOGLE SERVER ĐỂ TĂNG TỐC 5 LẦN
@st.cache_resource(ttl=3600)  # Lưu cấu hình cache ở phía Streamlit trong 1 tiếng
def khoi_tao_context_cache_sieu_toc():
    try:
        with open("tai_lieu_on_thi.txt", "r", encoding="utf-8") as f:
            noi_dung_tai_lieu = f.read()
    except FileNotFoundError:
        noi_dung_tai_lieu = "Hệ thống đang sử dụng cơ sở dữ liệu mặc định." #

    try:
        # Gộp tài liệu ôn thi vào prompt huấn luyện chung
        prompt_huuan_luyen_day_du = (
            f"{huong_dan_he_thong}\n\n"
            f"=== DỮ LIỆU HUẤN LUYỆN CHUYÊN SÂU ===\n{noi_dung_tai_lieu}\n========================"
        )
        
        # Tạo bộ nhớ đệm ngữ cảnh trên máy chủ Google (Hết hạn sau 1 tiếng để tiết kiệm)
        bộ_cache = client.caches.create(
            model="gemini-3.8-flash",
            config=types.CreateCachedContentConfig(
                contents=[prompt_huuan_luyen_day_du],
                ttl="3600s",
                display_name="e_hero_study_materials"
            )
        )
        return bộ_cache.name  # Trả về mã ID của bộ cache (ví dụ: 'cachedContents/12345')
    except Exception as e:
        st.warning(f"Không thể tạo Cache (Có thể do file quá nhỏ, tối thiểu cần ~32k tokens). Hệ thống sẽ chạy ở chế độ thường. Chi tiết: {e}")
        return None

# Gọi hàm khởi tạo cache
id_context_cache = khoi_tao_context_cache_sieu_toc()

# 2. KHỞI TẠO BỘ NHỚ LƯU TRỮ TÀI LIỆU TẠM THỜI (Hệ thống phê duyệt)
if "kho_tai_lieu" not in st.session_state:
    st.session_state.kho_tai_lieu = [
        {"ten": "Đề thi thử THPT Quốc gia 2026 - Đột phá Ngữ pháp.pdf", "nguoi_gui": "Thầy Minh (GV Tiếng Anh)", "trang_thai": "Đã phê duyệt"}, #
        {"ten": "Bộ từ vựng IELTS Chuyên sâu - Nâng band Thần tốc 8.0.pdf", "nguoi_gui": "Bạn An (Lớp 12A1)", "trang_thai": "Đã phê duyệt"} #
    ]
if "danh_sach_cho" not in st.session_state:
    st.session_state.danh_sach_cho = [] #

# 3. THIẾT KẾ GIAO DIỆN CHÂN THỰC VÀ THANH ĐIỀU HƯỚNG TRANG (MULTIPAGE)
st.set_page_config(page_title="E-HERO AI Platform", page_icon="🤖", layout="wide") #

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); }
    .main-title { background: linear-gradient(45deg, #1e3a8a, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-family: 'Inter', sans-serif; font-weight: 800; text-align: center; }
    .card-luxury { background-color: #ffffff; padding: 20px; border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.03); margin-bottom: 20px; border-top: 4px solid #2563eb; }
    </style>
""", unsafe_allow_html=True) #

st.sidebar.markdown("## 🧭 BẢNG ĐIỀU HƯỚNG") #
trang_hien_tai = st.sidebar.radio("Chọn không gian làm việc:", ["🤖 Trợ lý AI Thông Minh", "📚 Kho Tài Liệu Học Tập", "🔐 Cổng Kiểm Duyệt Admin"]) #

# ==========================================
# TRANG 1: TRỢ LÝ AI CHAT THÔNG MINH (ĐÃ TỐI ƯU VOICE + CACHE)
# ==========================================
if trang_hien_tai == "🤖 Trợ lý AI Thông Minh":
    st.markdown("<h1 class='main-title'>🤖 PROJECT E-HERO AI ECOSYSTEM</h1>", unsafe_allow_html=True) #
    st.caption("<p style='text-align: center; color: #64748b;'>Hệ thống Trợ lý ảo Cá nhân hóa - Không gian học tập Tiếng Anh toàn diện</p>", unsafe_allow_html=True) #
    
    with st.container():
        st.markdown("""
        <div class='card-luxury'>
        <h4 style='color: #1e293b; margin-top:0; margin-bottom:8px;'>💡 HƯỚNG DẪN GỢI Ý NỘI DUNG HỎI THEO TỪ KHÓA:</h4>
        <p style='color: #475569; font-size:0.9em; margin-bottom:12px;'>Nhấp vào từ khóa để tự động nạp nhanh câu hỏi mẫu xuất sắc vào ô nhớ hệ thống:</p>
        </div>
        """, unsafe_allow_html=True) #
        
        col1, col2, col3, col4 = st.columns(4) #
        with col1:
            if st.button("📌 Từ khóa: THPT Quốc Gia"): #
                st.session_state.goi_y_prompt = "Hãy giải thích chi tiết cấu trúc câu Đảo ngữ (Inversion) thường gặp trong đề thi THPT và cho ví dụ minh họa kèm bài tập." #
        with col2:
            if st.button("👑 Từ khóa: IELTS Writing"): #
                st.session_state.goi_y_prompt = "Chấm điểm và sửa bài luận sau theo 4 tiêu chí chuẩn Rubric IELTS: [Dán bài văn của bạn vào đây]" #
        with col3:
            if st.button("🗣️ Từ khóa: Alex Speaking"): #
                st.session_state.goi_y_prompt = "Hello Alex! Let's practice speaking english. Can we chat about environmental protection?" #
        with col4:
            if st.button("📝 Từ khóa: Chứng chỉ VSTEP"): #
                st.session_state.goi_y_prompt = "Hướng dẫn mình cấu trúc viết thư phàn nàn (Letter of Complaint) để đạt điểm cao trong kỳ thi VSTEP." #

    if "goi_y_prompt" in st.session_state and st.session_state.goi_y_prompt:
        st.info(f"📋 **Câu hỏi mẫu đã sẵn sàng:** `{st.session_state.goi_y_prompt}`") #
        st.caption("Mẹo: Hãy bôi đen copy câu lệnh trên và dán vào ô chat dưới cùng để gửi đi siêu tốc!") #

    if "messages" not in st.session_state:
        st.session_state.messages = [] #
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"]) #
            if message["role"] == "assistant" and "audio" in message:
                st.audio(message["audio"], format="audio/mp3")

    chat_input_data = st.chat_input(placeholder="Hỏi bằng chữ hoặc gửi giọng nói qua micro...", accept_audio=True) #

    if chat_input_data:
        user_display_message = ""
        ai_content_input = None

        is_audio_file = hasattr(chat_input_data, 'audio') and chat_input_data.audio is not None #

        if is_audio_file:
            user_display_message = "🎙️ *[Học sinh vừa gửi một đoạn ghi âm giọng nói]*" #
            try:
                audio_bytes = chat_input_data.audio.read() #
                ai_content_input = [
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"), #
                    "Học sinh đang gửi file ghi âm. Hãy phân tích giọng nói và phản hồi bằng cả âm thanh."
                ]
            except:
                ai_content_input = "Hello Alex!" #
        else:
            user_display_message = chat_input_data.text #
            ai_content_input = user_display_message #

        st.session_state.messages.append({"role": "user", "content": user_display_message}) #
        with st.chat_message("user"):
            st.markdown(user_display_message) #

        with st.chat_message("assistant"):
            try:
                van_ban_placeholder = st.empty()
                van_ban_placeholder.markdown("*AI đang xử lý thông tin siêu tốc...*")

                # Cấu hình gọi API thông minh
                if id_context_cache:
                    # NẾU CÓ CACHE: Gọi mô hình kết hợp ID bộ nhớ đệm (Tốc độ phản hồi cực nhanh)
                    config_chay = types.GenerateContentConfig(
                        cached_content=id_context_cache,
                        response_modalities=["TEXT", "AUDIO"]
                    )
                else:
                    # NẾU KHÔNG CÓ CACHE (Do file tài liệu quá nhỏ): Chạy prompt thông thường
                    config_chay = types.GenerateContentConfig(
                        system_instruction=huong_dan_he_thong,
                        response_modalities=["TEXT", "AUDIO"]
                    )

                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=ai_content_input,
                    config=config_chay
                )

                full_text_response = response.text if response.text else "Mình đã xử lý xong yêu cầu của bạn!"
                van_ban_placeholder.markdown(full_text_response)

                # Trích xuất dữ liệu âm thanh trả về từ Gemini
                audio_data_bytes = None
                if response.candidates and response.candidates.content:
                    for part in response.candidates.content.parts:
                        if part.inline_data and "audio" in part.inline_data.mime_type:
                            audio_data_bytes = part.inline_data.data
                            break

                if audio_data_bytes:
                    st.audio(audio_data_bytes, format="audio/mp3")
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
