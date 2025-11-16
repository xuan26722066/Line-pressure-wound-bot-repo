from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import os
import openai
from io import BytesIO
import uuid

# ===== 讀取環境變數 =====
openai.api_key = os.environ.get("OPENAI_API_KEY")

LINE_CHANNEL_ACCESS_TOKEN = "twHYAZUU5LxYZcM2gn2/Wzzn8FJSdpZaER077pGBrdjdHDqrpm/mvJskSLSjW9HpM1NFvHWjOhGQCo9B41fudwXM63lqNVSr0DT6F1vo8v6NwPe8oHLZJgb+lOwdr0aXTl+ITeTsaeY0wD2aBjGrpAdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "5b97caed1ccc3bd56cc6e2278b287273"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ===== 初始化 Flask =====
app = Flask(__name__)

# ===== Callback 路由 =====
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    print("收到 Webhook 訊息")
    print(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid Signature")
        abort(400)
    return 'OK'  # LINE 必須收到 200

# ===== 文字訊息處理 =====
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    print(f"收到文字：{event.message.text}")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="請傳壓傷照片給我，我會分析分級。")
    )

# ===== 圖片訊息處理 (GPT-4V 分級) =====
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    print("收到圖片！")

    # 1️⃣ 下載 LINE 圖片
    message_content = line_bot_api.get_message_content(event.message.id)
    image_bytes = BytesIO(message_content.content)

    # 2️⃣ 暫存圖片到 /tmp，產生唯一檔名
    file_name = f"/tmp/{str(uuid.uuid4())}.jpg"
    with open(file_name, "wb") as f:
        f.write(image_bytes.getbuffer())

    # 3️⃣ 產生 GPT 可讀 URL
    # Render /tmp 無法公開，建議換成 Imgur/S3 外部圖床
    # 這裡先用示意 URL，部署時需替換
    image_url = f"https://your-public-image-url.com/{file_name.split('/')[-1]}"
    print(f"圖片 URL: {image_url}")

    # 4️⃣ 呼叫 GPT-4V 分析圖片
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-v1",
            messages=[
                {"role": "system", "content": "你是一名護理師，負責判斷壓傷分級（1~4級）。"},
                {"role": "user", "content": f"分析這張圖片的壓傷分級，請直接告訴我 1～4 級。圖片 URL: {image_url}"}
            ]
        )

        ai_reply = response.choices[0].message["content"]
        print(f"GPT-4V 回覆：{ai_reply}")

    except Exception as e:
        ai_reply = "AI 分析失敗，請稍後再試。"
        print(f"GPT 呼叫錯誤：{e}")

    # 5️⃣ 回覆 LINE 使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"AI 分析結果：{ai_reply}")
    )

# ===== Flask 啟動 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
