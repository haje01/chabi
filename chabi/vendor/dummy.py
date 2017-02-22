from flask import Blueprint

from chabi import ChatbotBase


blueprint = Blueprint('dummy', __name__)


class DummyChatBot(ChatbotBase):
    def request_analyze(self, sender, msg):
        return None

    def handle_unknown(self, data):
        return False, None

    def handle_incomplete(self, data):
        return False, None


def init_dummy_chatbot(flask_app, access_token):
    DummyChatBot(flask_app, blueprint, access_token)
    return flask_app
