from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage

import os
from io import BytesIO
import cloudinary
import cloudinary.uploader
from openai import OpenAI
import json

# ===== Cloudinary 設定 =====
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
)

# ===== OpenAI Client =====
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ===== Flask =====
app = Flask(__name__)

# ===== LINE Bot Keys =====
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ===== Callback 路由 =====
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK", 200

# ===== 處理文字訊息 =====
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="請傳送壓傷照片，我會用 AI 幫你分析分級（1～4級）。")
    )

# ===== 處理圖片訊息 =====
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    try:
        # 1️⃣ 從 LINE 下載圖片
        content = line_bot_api.get_message_content(event.message.id)
        image_bytes = content.content

        # 2️⃣ 上傳到 Cloudinary
        upload_result = cloudinary.uploader.upload(
            BytesIO(image_bytes),
            folder="line-uploads",
            resource_type="image"
        )
        image_url = upload_result.get("secure_url")
        print("圖片已上傳至 Cloudinary:", image_url)

        # 3️⃣ 呼叫 GPT-4o 進行影像分析（使用固定 JSON 格式）
        prompt_system = (
            "你是一名專業護理師，負責判斷壓傷分級（1～4級）。\n"
            "分級標準：\n"
            "1級：皮膚完整但紅腫或疼痛\n"
            "2
