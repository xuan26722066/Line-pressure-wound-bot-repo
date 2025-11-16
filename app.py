from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import random
import os

# ===== 初始化 Flask =====
app = Flask(__name__)

# ===== LINE Bot 金鑰 (必須用雙引號包起來) =====
LINE_CHANNEL_ACCESS_TOKEN = "twHYAZUU5LxYZcM2gn2/Wzzn8FJSdpZaER077pGBrdjdHDqrpm/mvJskSLSjW9HpM1NFvHWjOhGQCo9B41fudwXM63lqNVSr0DT6F1vo8v6NwPe8oHLZJgb+lOwdr0aXTl+ITeTsaeY0wD2aBjGrpAdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "5b97caed1ccc3bd56cc6e2278b287273"
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ===== 壓傷分級模擬資料 =====
pressure_ulcer_levels = {
    1: "壓傷第1級：皮膚完整，但可能紅腫或疼痛",
    2: "壓傷第2級：部分皮膚破損，可能有水泡或淺層潰瘍",
    3: "壓傷第3級：皮膚全層破損，可能見到脂肪組織",
    4: "壓傷第4級：皮膚及組織深層破損，可能見到肌肉、骨頭或支撐結構"
}

# ===== Callback 路由 =====
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    # ===== Debug 訊息 =====
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

# ===== 圖片訊息處理 =====
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    print("收到圖片！")

    # 模擬 AI 分析
    level = random.randint(1, 4)
    ai_reply = pressure_ulcer_levels[level]

    print(f"回覆文字：{ai_reply}")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"AI 分析結果：{ai_reply}")
    )

# ===== Flask 啟動 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render 會提供環境變數 PORT
    app.run(host="0.0.0.0", port=port)
