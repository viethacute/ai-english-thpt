import streamlit as st
from google import genai
from google.genai import types
import time

# 1. CẤU HÌNH TRUY XUẤT CHÌA KHÓA AI BẢO MẬT TRÊN STREAMLIT SECRET KÉT SẮT
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

# 3. NẠP NÃO BỘ VÀ QUY TẮC TƯ DUY CHO AI (SYSTEM PROMPT CHUẨN)
prompt_he_thong = (
    "Bạn là Hệ sinh thái Trợ lý AI Tiếng Anh toàn diện dành cho học sinh THPT.\n"
    "Dưới đây là tài liệu chuyên sâu do nhóm tác giả nghiên cứu nạp vào để HUẤN LUYỆN bạn:\n"
    f"=== DỮ LIỆU HUẤN LUYỆN ===\n{du_lieu_huan_luyen}\n========================\n"
    "Quy trình xử lý theo phím tắt lệnh học sinh nhập:\n"
    "- Chế độ 1: Ôn thi THPT Quốc gia (Lệnh: /thpt): Giải đề chi tiết theo chuỗi tư duy (Chain-of-Thought), trích cấu trúc ngữ pháp SGK và tạo câu hỏi tương tự.\n"
    "- Chế độ 2: Luyện giao tiếp phản xạ (Lệnh: /speaking): Bạn đóng vai người bạn bản xứ tên Alex nói tiếng Anh dễ hiểu (A2-B1). "
    "Nếu nhận được FILE GHI ÂM giọng nói của học sinh, hãy lắng nghe, nhận xét cách phát âm và bắt buộc cung cấp mục [SỬA LỖI DIỄN ĐẠT] bằng tiếng Việt ở cuối đoạn thoại.\n"
    "- Chế độ 3: Chiến thần chứng chỉ (Lệnh: /ielts hoặc /vstep): Chấm bài viết luận theo 4 tiêu chí chuẩn quốc tế, gợi ý nâng cấp từ vựng.\n"
    "Luôn dùng tiếng Việt để giải thích ngữ pháp, ngôn ngữ thân thiện, sư phạm và động viên học sinh học tập."
)

# 4. THIẾT KẾ GIAO DIỆN LUXURY (MÀU SẮC CAO CẤP, BO GÓC KHỐI)
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

# Khối hướng dẫn UI/UX trực quan
with st.container():
    st.markdown("""
    <div class='guide-card'>
    <h4 style='color: #1e293b; margin-top:0;'>💡 TRÌNH ĐIỀU HƯỚNG TÁC VỤ NHANH:</h4>
    <p style='margin-bottom:8px;'><span class='badge-mode'>/thpt</span> Giải đề kiểm tra, chỉ lỗi sai và trích công thức SGK.</p>
    <p style='margin-bottom:8px;'><span class='badge-mode'>/speaking</span> Kích hoạt bạn Alex giao tiếp phản xạ nói qua Micro.</p>
    <p style='margin-bottom:0;'><span class='badge-mode'>/ielts</span> Chấm điểm Essay Rubric 4 tiêu chí quốc tế và sửa luận.</p>
    </div>
    """, unsafe_allow_html=True)

# Khởi tạo lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat dạng bong bóng Messenger
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. KHU VỰC NHẬP LIỆU ĐA PHƯƠNG THỨC NÂNG CAO ĐÃ SỬA LỖI (VÁ SẬP 100%)
# st.chat_input tự động trả về một đối tượng chứa thuộc tính text và audio khi có accept_audio=True
chat_input_data = st.chat_input(placeholder="Nhập chữ hoặc bấm biểu tượng Micro bên cạnh để nói...", accept_audio=True)

if chat_input_data:
    user_display_message = ""
    ai_content_input = None

    # Thuật toán bóc tách dữ liệu chuẩn hóa từ Streamlit API mới
    # Kiểm tra xem học sinh có gửi file ghi âm bằng Micro hay không
    is_audio_file = False
    if hasattr(chat_input_data, 'audio') and chat_input_data.audio is not None:
        is_audio_file = True
    elif isinstance(chat_input_data, dict) and chat_input_data.get('audio') is not None:
        is_audio_file = True

    # NẾU LÀ TIN NHẮN GIỌNG NÓI (VOICE)
    if is_audio_file:
        user_display_message = "🎙️ *[Học sinh vừa gửi một đoạn ghi âm giọng nói luyện Speaking]*"
        try:
            # Truy xuất tệp tin âm thanh thô an toàn bất chấp định dạng dictionary hay object
            audio_obj = chat_input_data.audio if hasattr(chat_input_data, 'audio') else chat_input_data['audio']
            audio_bytes = audio_obj.read() # Đọc mảng byte âm thanh
            
            # Đóng gói mảng byte âm thanh gửi trực tiếp lên não bộ Gemini theo chuẩn Google GenAI SDK
            ai_content_input = [
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                "Học sinh đang luyện nói tiếng Anh giao tiếp phản xạ. Hãy nghe đoạn ghi âm trên, phản hồi bằng tiếng Anh và sửa lỗi phát âm/ngữ pháp bằng tiếng Việt."
            ]
        except Exception as audio_err:
            user_display_message = "⚠️ *[Lỗi xử lý file âm thanh, hệ thống tự động chuyển sang nhận diện văn bản]*"
            ai_content_input = "/speaking Hello Alex!"
    
    # NẾU LÀ TIN NHẮN CHỮ (TEXT) THÔNG THƯỜNG
    else:
        # Lấy thuộc tính text từ đối tượng đầu vào
        user_display_message = chat_input_data.text if hasattr(chat_input_data, 'text') else str(chat_input_data)
        ai_content_input = user_display_message

    # Hiển thị tin nhắn của học sinh lên màn hình web
    st.session_state.messages.append({"role": "user", "content": user_display_message})
    with st.chat_message("user"):
        st.markdown(user_display_message)

    # GỬI LÊN CHO MÔ HÌNH THẾ HỆ MỚI GEMINI 3.8-FLASH XỬ LÝ (TÍCH HỢP CHỐNG LỖI QUÁ TẢI 503)
    with st.chat_message("assistant"):
        with st.spinner("E-HERO AI đang tư duy và xử lý ngôn ngữ..."):
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
                    break  # Thành công, thoát vòng lặp
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)  # Đợi máy chủ Google giảm tải rồi thử lại
                        continue
                    else:
                        st.error(f"Lỗi kết nối máy chủ AI: {str(e)}. Bạn vui lòng bấm nút Gửi lại nhé!")
                        break
