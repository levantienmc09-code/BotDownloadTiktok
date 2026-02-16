import telebot
import requests
import time
import re
import os
from flask import Flask, request
import threading

# Cấu hình bot
BOT_TOKEN = "8351128906:AAFCxpfZggdLDzJJQxxugUW4g4Hqf3awAdw"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Tạo Flask app
app = Flask(__name__)

TIKTOK_API = "https://tikwm.com/api/?url="


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(
        message,
        "• <b>Gửi Link Video Tiktok Để Tải •</b>"
    )


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Kiểm tra nếu tin nhắn có chứa http
    if 'http' in message.text:
        # Tìm URL trong tin nhắn
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.text)
        
        if urls:
            url = urls[0]  # Lấy URL đầu tiên
            process_tiktok(message, url)


def process_tiktok(message, url):
    try:
        # Gửi thông báo đang xử lý (in đậm)
        wait = bot.reply_to(message, "<b>🔄 Đang Xử Lí Video</b>")

        # Gọi API tikwm.com
        api_url = TIKTOK_API + url
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        res = requests.get(api_url, timeout=30, headers=headers)
        data = res.json()
        
        if data.get("code") != 0:
            bot.edit_message_text("❌ <b>Tải TikTok thất bại</b>", message.chat.id, wait.message_id)
            return

        # Lấy dữ liệu từ API
        video_data = data["data"]
        
        # Thông tin cơ bản
        title = video_data.get("title", "Không có tiêu đề")
        duration = video_data.get("duration", 0)
        play_url = video_data.get("play", "")  # Video không watermark
        size = video_data.get("size", 0)  # Size video không watermark

        # Thông tin tác giả
        author = video_data.get("author", {})
        nickname = author.get("nickname", "Unknown")
        unique_id = author.get("unique_id", "unknown")

        # Thông tin thống kê
        play_count = video_data.get("play_count", 0)
        digg_count = video_data.get("digg_count", 0)
        comment_count = video_data.get("comment_count", 0)
        share_count = video_data.get("share_count", 0)
        download_count = video_data.get("download_count", 0)
        collect_count = video_data.get("collect_count", 0)

        # Tạo caption theo đúng format yêu cầu
        caption = (
            "🎬 <b>TIKTOK DOWNLOADER</b>\n\n"
            f"📌 <b>Tiêu đề:</b> {title}\n"
            f"👤 <b>Tác giả:</b> {nickname} (@{unique_id})\n"
            f"⏱ <b>Thời lượng:</b> {duration}s\n"
            f"📦 <b>Dung lượng:</b> {round(size / 1024 / 1024, 2)} MB\n\n"
            "📊 <b>Thống kê</b>\n"
            f"▶️ View: {play_count:,}\n"
            f"❤️ Like: {digg_count:,}\n"
            f"💬 Comment: {comment_count:,}\n"
            f"🔁 Share: {share_count:,}\n"
            f"📥 Download: {download_count:,}\n"
            f"📌 Collect: {collect_count:,}"
        )

        # ===== GỬI VIDEO =====
        try:
            bot.send_video(
                chat_id=message.chat.id,
                video=play_url,
                caption=caption,
                supports_streaming=True,
                timeout=60
            )
        except Exception as e:
            # Nếu gửi video lỗi, gửi link tải
            bot.send_message(
                message.chat.id,
                f"⚠️ <b>Không gửi được video, bạn có thể tải trực tiếp:</b>\n"
                f"📥 <a href='{play_url}'>Tải video tại đây</a>"
            )

        # Xóa thông báo đang xử lý
        bot.delete_message(message.chat.id, wait.message_id)

    except requests.exceptions.RequestException as e:
        error_msg = f"❌ <b>Lỗi kết nối:</b> Không thể kết nối đến API TikTok\n"
        error_msg += f"<code>{str(e)}</code>"
        
        try:
            bot.edit_message_text(error_msg, message.chat.id, wait.message_id)
        except:
            bot.reply_to(message, error_msg)
            
    except Exception as e:
        error_msg = f"⚠️ <b>Lỗi:</b> <code>{str(e)}</code>\n"
        error_msg += "Vui lòng thử lại hoặc dùng link khác."
        
        try:
            bot.edit_message_text(error_msg, message.chat.id, wait.message_id)
        except:
            bot.reply_to(message, error_msg)


# Route để web server hoạt động
@app.route('/')
def index():
    return "🤖 TikTok Bot is running!", 200


@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200


# Hàm chạy bot với polling
def run_bot():
    print("🤖 TikTok Bot đang chạy...")
    print("📝 Đang sử dụng API: tikwm.com")
    bot.infinity_polling()


if __name__ == '__main__':
    # Lấy port từ biến môi trường (Render sẽ set PORT)
    port = int(os.environ.get('PORT', 5000))
    
    # Chạy bot trong một thread riêng
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Chạy web server
    print(f"🌐 Web server đang chạy trên port {port}...")
    app.run(host='0.0.0.0', port=port)
