from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage

import os
import openai
import base64
from io import BytesIO

# ====== OpenAI Key ======
openai.api_key = os.environ.get("OPENAI_API_KEY")

# ====== Flask ======
app = Flask(__name__)

# ====== LINE Bot Keys ======
LINE_CHANNEL_ACCESS_TOKEN = "twHYAZUU5LxYZcM2gn2/Wzzn8FJSdpZaER077pGBrdjdHDqrpm/mvJskSLSjW9HpM1NFvHWjOhGQCo9B41fudwXM63lqNVSr0DT6F1vo8v6NwPe8oHLZJgb+lOwdr0aXTl+ITeTsaeY0wD2aBjGrpAdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "5b97caed1ccc3bd56cc6e2278b287273"
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# ===== Callback 路由 =====
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    print("收到 Webhook")
    print(body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("簽章錯誤！")
        abort(400)

    return 'OK'


# ===== 文字訊息處理 =====
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_msg = event.message.text
    print("收到文字：", user_msg)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="請傳送壓傷照片，我會使用 AI 幫你分析壓傷分級（1～4級）。")
    )


# ===== 圖片訊息處理 =====
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    print("收到圖片！")

    # 1️⃣ 從 LINE 下載圖片
    message_content = line_bot_api.get_message_content(event.message.id)
    image_bytes = message_content.content  # ← 真正的圖片 bytes

    # 2️⃣ 圖片轉 Base64（OpenAI 需要）
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # 3️⃣ 呼叫 GPT-4o-mini / GPT-4o 分析壓傷
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",   # 可改成 gpt-4o, gpt-4.1, gpt-4.1-mini
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text",
                         "text": "請你根據這張圖片判斷壓傷分級（1～4級），並說明原因。"},
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

        ai_reply = response.choices[0].message["content"]
        print("AI 回覆：", ai_reply)

    except Exception as e:
        print("AI 出錯：", e)
        ai_reply = "AI 分析失敗，請稍後再試。"

    # 4️⃣ 回覆給使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"AI 分析結果：\n{ai_reply}")
    )


# ===== Flask 啟動（Render 強制用 0.0.0.0） =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
