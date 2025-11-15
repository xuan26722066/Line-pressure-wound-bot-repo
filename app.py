from flask import Flask, request, abort, jsonify
import os
import hmac
import hashlib
import base64
import requests

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

LINE_REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
LINE_CONTENT_ENDPOINT = 'https://api-data.line.me/v2/bot/message/{messageId}/content'


def verify_signature(request_body, signature):
    hash_value = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), request_body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash_value).decode('utf-8')
    return hmac.compare_digest(expected_signature, signature)


def analyze_image_with_ai(image_bytes):
    # 目前是示範用的假回覆，你之後可以改成 AI 模型判讀
    return {
        "grade": "Stage 2",
        "confidence": 0.85,
        "note": "這是範例結果，你可以之後改成真的 AI 判讀"
    }


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data()

    if not verify_signature(body, signature):
        abort(400)

    events = request.json.get('events', [])
    for event in events:
        if event.get('type') != 'message':
            continue

        message = event.get('message', {})
        if message.get('type') != 'image':
            continue

        reply_token = event.get('replyToken')
        message_id = message.get('id')

        # 抓取圖片
        headers = {'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'}
        content_url = LINE_CONTENT_ENDPOINT.format(messageId=message_id)
        image_response = requests.get(content_url, headers=headers)

        if image_response.status_code != 200:
            reply_text = "圖片下載失敗"
        else:
            image_bytes = image_response.content
            ai_result = analyze_image_with_ai(image_bytes)

            reply_text = (
                f"壓傷分級：{ai_result['grade']}\n"
                f"信心度：{ai_result['confidence']}\n"
                f"備註：{ai_result['note']}"
            )

        # 回覆給使用者
        reply_data = {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": reply_text}]
        }

        requests.post(LINE_REPLY_ENDPOINT,
                      headers={
                          "Content-Type": "application/json",
                          "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
                      },
                      json=reply_data)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000)
