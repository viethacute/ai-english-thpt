import streamlit as st
from google import genai
from google.genai import types

# 1. CẤU HÌNH TRUY XUẤT CHÌA KHÓA AI BẢO MẬT TRÊN CLOUD
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Chưa cấu hình API Key trong mục Secrets của hệ thống máy chủ.")

# 2. ĐỌC DỮ LIỆU ĐỂ HUẤN LUYỆN BOT TỰ ĐỘNG TỪ FILE TEXT
try:
    with open("tai_lieu_on_thi.txt", "r", encoding="utf-8") as f:
        du_lieu_huan_luyen = f.read()
except FileNotFoundError:
    du_lieu_huan_luyen = "Hệ thống đang sử dụng cơ sở dữ liệu mặc định."

# 3. NẠP NÃO BỘ VÀ QUY TẮC TƯ DUY CHO AI
prompt_he_thong = (
    "Bạn là Hệ sinh thái Trợ lý AI Tiếng Anh toàn diện dành cho học sinh THPT.\n"
    "Dưới đây là tài liệu chuyên sâu do nhóm tác giả nghiên cứu và nạp vào để HUẤN LUYỆN bạn. "
    "Bạn phải học thuộc và ưu tiên tuyệt đối việc sử dụng kiến thức này để giải đáp cho học sinh:\n"
    f"=== DỮ LIỆU HUẤN LUYỆN ===\n{du_lieu_huan_luyen}\n========================\n"
    "Quy trình xử lý theo phím tắt lệnh:\n"
    "- Chế độ 1: Ôn thi THPT Quốc gia (Lệnh: /thpt): Giải đề chi tiết theo chuỗi tư duy (Chain-of-Thought), trích cấu trúc ngữ pháp SGK và tạo câu hỏi tương tự.\n"
    "- Chế độ 2: Luyện giao tiếp phản xạ (Lệnh: /speaking): Đóng vai người bạn bản xứ tên Alex nói tiếng Anh dễ hiểu, sửa lỗi diễn đạt ở cuối câu thoại bằng tiếng Việt.\n"
    "- Chế độ 3: Chiến thần chứng chỉ (Lệnh: /ielts hoặc /vstep): Chấm bài viết luận theo 4 tiêu chí chuẩn quốc tế, gợi ý nâng cấp từ vựng.\n"
    "Luôn dùng tiếng Việt để giải thích, thân thiện, sư phạm và động viên học sinh."
)

# 4. GIAO DIỆN WEB PHÒNG CHAT ĐẸP VÀ CHUYÊN NGHIỆP
st.set_page_config(page_title="AI Tiếng Anh THPT", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    .main-title { color: #1e3a8a; font-family: 'Inter', sans-serif; font-weight: 800; text-align: center; margin-bottom: 5px; }
    .guide-box { background-color: #ffffff; padding: 15px; border-radius: 12px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🤖 HỆ SINH THÁI AI TRỢ LÝ TIẾNG ANH TOÀN DIỆN</h1>", unsafe_allow_html=True)
st.caption("<p style='text-align: center; color: #64748b;'>Đề tài Nghiên cứu KHKT - Đạt chuẩn giao diện UI/UX tối ưu</p>", unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div class='guide-box'>
    <b>💡 HƯỚNG DẪN CÁC PHÍM TẮT LỆNH ĐIỀU HƯỚNG NHANH:</b><br>
    • Gõ <b>/thpt + Câu hỏi</b> để vào chế độ Giải đề thi thử và xem cấu trúc ngữ pháp.<br>
    • Gõ <b>/speaking + Câu thoại</b> để trò chuyện phản xạ và nhận bảng sửa lỗi từ bạn Alex.<br>
    • Gõ <b>/ielts + Bài văn</b> để Giám khảo chấm điểm theo tiêu chí chuẩn quốc tế.
    </div>
    """, unsafe_allow_html=True)

# Khởi tạo lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị bong bóng chat mượt mà giống Messenger/ChatGPT
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ô nhập tin nhắn cố định dưới màn hình web
if prompt := st.chat_input("Nhập câu hỏi học tập hoặc dán đề thi tại đây..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Hệ thống đang truy xuất kho dữ liệu huấn luyện..."):
            try:
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(system_instruction=prompt_he_thong)
                )
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Lỗi xử lý hệ thống: {str(e)}")
