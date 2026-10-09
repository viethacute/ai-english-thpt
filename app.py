import gradio as gr
from google import genai
from google.genai import types

# 1. CẤU HÌNH API KEY MIỄN PHÍ THEO THƯ VIỆN GOOGLE MỚI NHẤT
# Hãy thay dãy chữ dưới đây bằng mã API Key bạn lấy ở Google AI Studio nhé
GEMINI_API_KEY = "DÁN_MÃ_API_KEY_THẬT_CỦA_BẠN_VÀO_ĐÂY"
client = genai.Client(api_key=M_API_KEY)

# 2. NÃO BỘ VÀ QUY TẮC TƯ DUY CHO AI (SYSTEM PROMPT)
prompt_he_thong = (
    "Bạn là Hệ sinh thái Trợ lý AI Tiếng Anh toàn diện dành cho học sinh THPT.\n"
    "Học sinh sẽ gõ các phím tắt lệnh để chọn chế độ học tập:\n"
    "- Chế độ 1: Ôn thi THPT Quốc gia (Lệnh: /thpt): Giải đề chi tiết theo chuỗi tư duy (Chain-of-Thought), trích cấu trúc ngữ pháp SGK và tạo bài tập tương tự.\n"
    "- Chế độ 2: Luyện giao tiếp phản xạ (Lệnh: /speaking): Đóng vai người bạn bản xứ tên Alex nói tiếng Anh dễ hiểu, sửa lỗi diễn đạt ở cuối câu thoại bằng tiếng Việt.\n"
    "- Chế độ 3: Chiến thần chứng chỉ (Lệnh: /ielts hoặc /vstep): Chấm bài viết luận theo 4 tiêu chí chuẩn quốc tế, gợi ý nâng cấp từ vựng.\n"
    "Luôn dùng tiếng Việt để giải thích, thân thiện, sư phạm và động viên học sinh."
)

# 3. THUẬT TOÁN XỬ LÝ TIN NHẮN CHAT THEO CHUẨN MỚI
def phan_hoi_ai(message, history):
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash', # Sử dụng dòng mô hình thế hệ mới nhất siêu tốc
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=prompt_he_thong
            )
        )
        return response.text
    except Exception as e:
        return f"Lỗi kết nối AI: {str(e)}. Hãy kiểm tra lại mã API Key của bạn."

# 4. THIẾT KẾ GIAO DIỆN PHÒNG CHAT ĐẸP CHUẨN GRADIO MỚI
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 HỆ SINH THÁI AI TRỢ LÝ TIẾNG ANH TOÀN DIỆN")
    gr.Markdown("### Sản phẩm nghiên cứu Khoa học Kỹ thuật độc lập - Trường THPT")
    
    gr.ChatInterface(
        fn=phan_hoi_ai,
        chatbot=gr.Chatbot(height=500, placeholder="🤖 *Trợ lý AI đã sẵn sàng! Hãy nhập câu hỏi hoặc gõ lệnh /thpt, /speaking, /ielts để bắt đầu...*"),
        textbox=gr.Textbox(placeholder="Nhập nội dung ôn thi hoặc nhập lệnh chuyển chế độ...", container=False, scale=7),
        submit_btn="Gửi 🚀",
        stop_btn="Dừng 🛑"
    )

# Áp dụng giao diện Soft theme theo đúng quy chuẩn Gradio mới tại hàm launch
if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), share=True)
