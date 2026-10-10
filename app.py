import streamlit as st
from google import genai
from google.genai import types
import time  # Nạp thêm thư viện thời gian để đếm giây thử lại tự động

# 1. CẤU HÌNH TRUY XUẤT CHÌA KHÓA AI BẢO MẬT
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
    "Dưới đây là tài liệu chuyên sâu do nhóm tác giả nghiên cứu nạp vào để HUẤN LUYỆN bạn:\n"
    f"=== DỮ LIỆU HUẤN LUYỆN ===\n{du_lieu_huan_luyen}\n========================\n"
    "Quy trình xử lý theo phím tắt lệnh:\n"
    "- /thpt: Giải đề chi tiết theo chuỗi tư duy (Chain-of-Thought), trích cấu trúc ngữ pháp SGK và tạo câu hỏi tương tự.\n"
    "- /speaking: Đóng vai người bạn bản xứ tên Alex nói tiếng Anh dễ hiểu, "
    "bắt buộc cung cấp mục [SỬA LỖI DIỄN ĐẠT] bằng tiếng Việt ở cuối đoạn thoại.\n"
    "- /ielts hoặc /vstep: Chấm bài viết luận theo 4 tiêu chí chuẩn quốc tế, gợi ý nâng cấp từ vựng.\n"
    "Luôn dùng tiếng Việt để giải thích, thân thiện, sư phạm và động viên học sinh."
)

# 4. THIẾT KẾ GIAO DIỆN LUXURY (TÂN TRANG DIỆN MẠO)
st.set_page_config(page_title="E-HERO AI Ecosystem", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); }
    .main-title { 
        background: linear-gradient(45deg, #1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Inter', sans-serif; 
        font-weight: 800; 
        text-align: center; 
        margin-bottom: 2px;
        letter-spacing: -1px;
    }
    .guide-card { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 16px; 
        border-left: 6px solid #2563eb; 
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.04); 
        margin-bottom: 25px; 
    }
    .badge-mode {
        background-color: #eff6ff;
        color: #1d4ed8;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85em;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🤖 PROJECT E-HERO AI ECOSYSTEM</h1>", unsafe_allow_html=True)
st.caption("<p style='text-align: center; color: #64748b; font-weight: 500;'>Nền tảng Trợ lý ảo Cá nhân hóa Giáo dục Ngoại ngữ - Phiên bản 2026</p>", unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div class='guide-card'>
    <h4 style='color: #1e293b; margin-top:0;'>💡 TRÌNH ĐIỀU HƯỚNG TÁC VỤ NHANH:</h4>
    <p style='margin-bottom:8px;'><span class='badge-mode'>/thpt</span> Giải đề kiểm tra, chỉ lỗi sai và trích công thức SGK.</p>
    <p style='margin-bottom:8px;'><span class='badge-mode'>/speaking</span> Kích hoạt bạn Alex giao tiếp phản xạ nói qua Micro.</p>
    <p style='margin-bottom:0;'><span class='badge-mode'>/ielts</span> Chấm điểm Essay Rubric 4 tiêu chí quốc tế và sửa luận.</p>
    </div>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. KHU VỰC NHẬP LIỆU CHUẨN ĐÃ ĐƯỢC VÁ LỖI AN TOÀN
chat_input_data = st.chat_input(placeholder="Nhập chữ hoặc bấm biểu tượng Micro bên cạnh để nói chuyện...", accept_audio=True)

if chat_input_data:
    user_message = ""
    ai_content_input = None

    is_audio = False
    try:
        if hasattr(chat_input_data, 'audio') and chat_input_data.audio:
            is_audio = True
        elif isinstance(chat_input_data, dict) and 'audio' in chat_input_data and chat_input_data['audio']:
            is_audio = True
    except:
        pass

    if is_audio:
        user_message = "🎙️ [Học sinh vừa gửi một tin nhắn bằng giọng nói]"
        try:
            audio_bytes = chat_input_data.audio.read() if hasattr(chat_input_data, 'audio') else chat_input_data['audio'].read()
            ai_content_input = [
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                prompt_he_thong + "\n\nHọc sinh đang gửi giọng nói nói phản xạ ở chế độ /speaking."
            ]
        except:
            user_message = "🎙️ [Giao tiếp giọng nói văn bản]"
            ai_content_input = "/speaking " + str(chat_input_data)
    else:
        user_message = chat_input_data.text if hasattr(chat_input_data, 'text') else str(chat_input_data)
        ai_content_input = user_message

    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    # THUẬT TOÁN TỰ ĐỘNG THỬ LẠI KHI MÁY CHỦ GOOGLE QUÁ TẢI (ANTI-503 lỗi)
    with st.chat_message("assistant"):
        with st.spinner("E-HERO AI đang truy xuất kho dữ liệu huấn luyện và xử lý..."):
            max_retries = 3  # Thử lại tối đa 3 lần nếu Google báo bận
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=ai_content_input,
                        config=types.GenerateContentConfig(system_instruction=prompt_he_thong)
                    )
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    break  # Thành công thì thoát khỏi vòng lặp ngay
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)  # Đợi 2 giây để máy chủ ổn định rồi thử lại
                        continue
                    else:
                        st.error(f"Hệ thống đang quá tải, bạn vui lòng nhấn Gửi lại câu hỏi nhé! Chi tiết: {str(e)}")
                        break
