from flask import request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import FollowEvent, MessageEvent, TextMessageContent

from config import LINE_CHANNEL_SECRET
from line_bot.message_handler import handle_follow, handle_text_message

handler = WebhookHandler(LINE_CHANNEL_SECRET)


def register_line_webhook(app):
    @app.route("/callback", methods=["POST"])
    def callback():
        signature = request.headers.get("X-Line-Signature", "")
        body = request.get_data(as_text=True)

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)

        return "OK"


@handler.add(FollowEvent)
def on_follow(event):
    handle_follow(event)


@handler.add(MessageEvent, message=TextMessageContent)
def on_message(event):
    handle_text_message(event)
