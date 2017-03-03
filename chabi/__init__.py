import time
import json

from flask import current_app as ca


def analyze_and_action(sender_id, msg_text):
    """Analyze message and do action for the result.

    Note:
        `request_analyze` of Chatbot Wrapper, analyzes messages via ChatBot
            API.
        `handle_action` of Chatbot Wrapper, check for a action need to be done.
        `handle_incomplete` of ChatBot Wrapper, handles entity filling message.
        `handle_unknown` of Chatbot Wrapper, handles unknown messages from
            user.
        `extract_text_msg` of Chatbot, extract text message part from Chatbot
            API return.

    Returns:
        dict: Handled result (contains return message)
    """
    st = time.time()
    ca.logger.debug('analyzing start: {}'.format(msg_text))
    res = ca.chatbot.request_analyze(sender_id, msg_text)
    ca.logger.debug('analyzing elapsed: {0:.2f}'.format(time.time() - st))
    if res is None:
        return

    if type(res) is not str:
        res = res.read()
    data = json.loads(res)

    # check unknown message
    unknown, res = ca.chatbot.handle_unknown(data)
    if unknown:
        ca.logger.info("unknown message: {}".format(res))
        return res

    # check action needs to be done
    action_done, res = ca.chatbot.handle_action(data)
    if action_done:
        ca.logger.info("action '{}' done".format(action_done))
        return res

    # check entity filling
    incomplete, res = ca.chatbot.handle_incomplete(data)
    if incomplete:
        ca.logger.info("incomplete message: {}".format(res))
        return res

    # default reply
    return ca.chatbot.extract_text_msg(data)


class CommonBase(object):

    def __init__(self, app):
        """Init common base.

        Args:
            app: A Flask app instance.
        """
        self.app = app
        self.logger = app.logger


class ChatbotBase(CommonBase):

    def __init__(self, app, blueprint, access_token):
        """Init chatbot base.

        Args:
            app: A Flask app instance.
            blueprint: Flask blueprint for url routing.
            access_token: Chatbot API access token.
        """
        super(ChatbotBase, self).__init__(app)
        app.chatbot = self
        app.register_blueprint(blueprint)

        self.access_token = access_token

    def request_analyze(self, sender_id, msg):
        raise NotImplementedError()

    def handle_action(self, data):
        raise NotImplementedError()

    def handle_unknown(self):
        raise NotImplementedError()

    def handle_incomplete(self):
        raise NotImplementedError()

    def extract_text_msg(self, data):
        raise NotImplementedError()


class MessengerBase(CommonBase):

    def __init__(self, app, blueprint, page_access_token, verify_token):
        """Init messenger base.

        Args:
            app: A Flask app instance.
        """
        super(MessengerBase, self).__init__(app)
        app.msgn = self
        app.register_blueprint(blueprint)

        self.app = app
        self.page_access_token = page_access_token
        self.verify_token = verify_token

    def get_text_msg(self, msg_event):
        raise NotImplementedError()

    def send_message(self, recipient_id, res):
        raise NotImplementedError()

    def ask_enter_text_msg(self, recipient_id):
        """Prompt user to enter only text message.

        Return:
            str: Return message content.
        """
        msg = dict(message=dict(text="Please enter text message."))
        self.send_message(recipient_id, msg)
        return msg

    def handle_msg_data(self, data):
        raise NotImplementedError()

    def reply_text_message(self, app, sender_id, mevent):
        raise NotImplementedError()

    def handle_account_link(self, auth_code):
        raise NotImplementedError()

    def handle_account_unlink(self):
        raise NotImplementedError()


class EventHandlerBase(CommonBase):

    def __init__(self, app):
        """Init event handler base.

        Args:
            app: A Flask app instance.
        """
        super(EventHandlerBase, self).__init__(app)
        app.evth = self

    def handle_action(self, msg):
        raise NotImplementedError()

    def handle_postback(self, msg):
        raise NotImplementedError()
