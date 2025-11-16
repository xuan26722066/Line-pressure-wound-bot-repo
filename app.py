from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
from io import BytesIO
import random
import os

app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']  # 取得 LINE 簽名
    body = request.get_data(as_text=True)            # 取得訊息內容
    print("收到 Webhook 訊息")                        # Debug log
    try:
        handler.handle(body, signature)             # 交給 LINE SDK 處理
    except InvalidSignatureError:
        print("Invalid Signature")                  # Debug log
        abort(400)                                  # LINE 收不到錯誤訊息
    return 'OK'                                     # 成功回傳 200


# ===== LINE Bot 金鑰 =====
LINE_CHANNEL_ACCESS_TOKEN = "twHYAZUU5LxYZcM2gn2/Wzzn8FJSdpZaER077pGBrdjdHDqrpm/mvJskSLSjW9HpM1NFvHWjOhGQCo9B41fudwXM63lqNVSr0DT6F1vo8v6NwPe8oHLZJgb+lOwdr0aXTl+ITeTsaeY0wD2aBjGrpAdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "5b97caed1ccc3bd56cc6e2278b287273"
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
    print("收到 Webhook 訊息")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid Signature")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    print(f"收到文字：{event.message.text}")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="請傳壓傷照片給我，我會分析分級。")
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    print("收到圖片！")
    # 立即回覆文字，先保證 LINE 收到 200
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="圖片收到，AI 分析中...")
    )
    


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
