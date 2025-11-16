from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage

import os
from io import BytesIO
import cloudinary
import cloudinary.uploader
from openai import OpenAI

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
        # 1️⃣ 下載 LINE 圖片
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

        # 3️⃣ GPT-4o 分析圖片
        system_prompt = (
            "你是一名專業護理師，負責判斷壓傷分級（1～4級）。"
            "請嚴格依照壓傷分級特徵比對，不能隨機猜測。"
            "若圖片不是傷口或無法判斷 → 回覆『無法判斷或非壓傷』。"
        )

        user_prompt = [
            {
                "type": "text",
                "text": (
                    "請依照以下流程判斷壓傷：\n"
                    "步驟1：判斷是否看得清楚皮膚表面，若否 → 回覆『無法判斷或非壓傷』。\n"
                    "步驟2：逐項比對壓傷特徵：\n"
                    "【第一級】完整皮膚、紅或粉紅、按壓不變白\n"
                    "【第二級】表皮破損或淺層傷口、水泡可能存在、淺紅濕潤\n"
                    "【第三級】皮膚全層破損、可見脂肪層、傷口較深但未見肌肉或骨頭\n"
                    "【第四級】深層組織破壞，可見肌肉、肌腱或骨頭\n"
                    "步驟3：回覆格式：\n"
                    "是否為壓傷：是/否\n"
                    "分級（若不符合特徵 → 無法判斷）\n"
                    "列出比對到的特徵\n"
                    "不要推測或亂回答\n"
                    f"請分析以下圖片： {image_url}"
                )
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        ai_text = response.choices[0].message["content"]
        print("GPT 回覆:", ai_text)

    except Exception as e:
        print("錯誤：", e)
        ai_text = "AI 分析失敗，請稍後再試。"

    # 4️⃣ 回覆使用者
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_text))

# ===== 啟動 Flask =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
