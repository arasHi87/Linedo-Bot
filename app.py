from flask import Flask, request, abort

from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (TextMessage, MessageEvent, PostbackEvent)
from config.config import (LINE_ACCESS_TOKEN, LINE_SECRET)

from logger import logger
from command import command
from parsers import WENKUParser

app = Flask(__name__)

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return 'OK'


# messange type
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    command(event.message.text, line_bot_api, event)


# postback type
@handler.add(PostbackEvent)
def handle_postback(event):
    command(event.postback.data, line_bot_api, event)


if __name__ == "__main__":
    app.run()
