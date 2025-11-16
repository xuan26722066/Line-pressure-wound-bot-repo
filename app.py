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

# ===== 壓傷分級詳細描述 =====
prompt_system = """
你是一名專業護理師，負責判斷壓傷分級（1～4級）。
分級標準如下：
1級：皮膚完整，但可能有紅腫或輕微疼痛
2級：部分皮膚破損，可能有水泡或淺層潰瘍，僅影響表皮及真皮
3級：皮膚全層破損，可能見到脂肪組織，傷口邊緣明顯
4級：皮膚及組織深層破損，可能見到肌肉、骨頭或支撐結構
請嚴格依照以上特徵判斷圖片的分級。
回覆格式僅使用 JSON：
{"level": X, "reason": "圖片中符合的特徵描述"}
"""

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

        # 3️⃣ 呼叫 GPT-4o-mini 進行影像分析
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,  # 降低隨機性
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": [
                    {"type": "text", "text": "請分析下圖壓傷分級，並依 JSON 格式輸出。"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]}
            ]
        )

        # 4️⃣ 取得 AI 回覆
        ai_text = response.choices[0].message["content"]
        print("GPT 回覆:", ai_text)

    except Exception as e:
        print("錯誤：", e)
        ai_text = "AI 分析失敗，請稍後再試。"

    # 5️⃣ 回覆使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"AI 分析結果：\n{ai_text}")
    )

# ===== 啟動 Flask =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
