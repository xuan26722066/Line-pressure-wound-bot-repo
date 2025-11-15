from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import requests
from io import BytesIO
import random

app = Flask(__name__)

# ===== LINE Bot 金鑰 =====
LINE_CHANNEL_ACCESS_TOKEN = twHYAZUU5LxYZcM2gn2/Wzzn8FJSdpZaER077pGBrdjdHDqrpm/mvJskSLSjW9HpM1NFvHWjOhGQCo9B41fudwXM63lqNVSr0DT6F1vo8v6NwPe8oHLZJgb+lOwdr0aXTl+ITeTsaeY0wD2aBjGrpAdB04t89/1O/w1cDnyilFU=
LINE_CHANNEL_SECRET = 5b97caed1ccc3bd56cc6e2278b287273
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 壓傷分級模擬資料
pressure_ulcer_levels = {
    1: "壓傷第1級：皮膚完整，但可能紅腫或疼痛",
    2: "壓傷第2級：部分皮膚破損，可能有水泡或淺層潰瘍",
    3: "壓傷第3級：皮膚全層破損，可能見到脂肪組織",
    4: "壓傷第4級：皮膚及組織深層破損，可能見到肌肉、骨頭或支撐結構"
}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="請傳壓傷照片給我，我會分析分級。")
    )

# 處理圖片訊息
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # 取得圖片內容
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = BytesIO(message_content.content)
    
    # ===== 模擬 AI 分析結果 =====
    # 這裡隨機產生分級，也可以改成 GPT-4V 或其他模型
    level = random.randint(1, 4)
    ai_reply = pressure_ulcer_levels[level]
    
    # 回覆 LINE 使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"AI 分析結果：{ai_reply}")
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
