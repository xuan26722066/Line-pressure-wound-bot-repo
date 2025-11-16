from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage

import os
import base64
from openai import OpenAI

# ===== OpenAI Client =====
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ===== Flask =====
app = Flask(__name__)

# ===== LINE Bot Keys（從 Render 環境變數讀） =====
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# ===== Callback =====
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return abort(400)

    return "OK", 200


# ===== Text Message =====
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    reply = "請傳送壓傷照片，我會用 AI 協助判斷分級（1～4級）。"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


# ===== Image Message =====
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    try:
        # 1. 下載圖片
        content = line_bot_api.get_message_content(event.message.id)
        image_bytes = content.content

        # 2. Base64 編碼
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # 3. 呼叫 OpenAI（gpt-4o-mini）
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "請依圖片判斷壓傷分級（1～4級），並簡述理由。"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
        )

        # 4. 取得 AI 回覆
        ai_text = response.choices[0].message["content"]

    except Exception as e:
        print("AI 錯誤：", e)
        ai_text = "AI 分析失敗，請稍後再試。"

    # 5. 回覆使用者
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_text))



# ===== Run =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
