import time
import json

from flask import current_app as ca


def analyze_and_action(sender_id, msg_text):
    """Analyze message and do action for the result.

    Note:
        `request_analyze` of ChatBot Wrapper, analyzes messages via ChatBot
            API.
        `handle_incomplete` of ChatBot Wrapper, handles entity filling message.
        `handle_unknown` of ChatBot Wrapper, handles unknown messages from
            user.
        `do_action` of App, do action for analyzed result from ChatBot API.

    Returns:
        dict: Handled or action result (contains return message)
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

    # check action needs to be done
    st = time.time()
    result = data['result']
    action = result['action']
    if len(action) > 0 and 'actionIncomplete' in result and\
            not result['actionIncomplete']:
        ca.logger.debug("action '{}' start: {}".format(action, data))
        res = ca.do_action(data)
        ca.logger.debug("action result: {}".format(res))
        ca.logger.debug('action elapsed: {0:.2f}'.format(time.time() - st))
        return res

    # check entity filling
    incomplete, res = ca.chatbot.handle_incomplete(data)
    if incomplete:
        ca.logger.info("incomplete message: {}".format(res))
        return res

    # check unknown message
    unknown, res = ca.chatbot.handle_unknown(data)
    if unknown:
        ca.logger.info("unknown message: {}".format(res))
        return res

    # normal reply
    if 'fulfillment' in result and len(result['fulfillment']) > 0:
        msg = result['fulfillment']
    else:
        msg = None
    return msg


class CommonBase(object):

    def __init__(self, flask_app):
        self.logger = flask_app.logger


class ChatbotBase(CommonBase):
    def __init__(self, flask_app, blueprint, access_token):
        super(ChatbotBase, self).__init__(flask_app)
        flask_app.chatbot = self
        flask_app.register_blueprint(blueprint)

        self.access_token = access_token

    def request_analyze(self, sender_id, msg):
        raise NotImplementedError()

    def handle_unknown(self):
        raise NotImplementedError()

    def handle_incomplete(self):
        raise NotImplementedError()


class MessengerBase(CommonBase):

    def __init__(self, flask_app, blueprint, page_access_token, verify_token):
        super(MessengerBase, self).__init__(flask_app)
        flask_app.msgn = self
        flask_app.register_blueprint(blueprint)

        self.app = flask_app
        self.page_access_token = page_access_token
        self.verify_token = verify_token

    def get_text_msg(self, msg_event):
        raise NotImplementedError()

    def send_message(self, recipient_id, res):
        raise NotImplementedError()

    def ask_enter_text_msg(self, recipient_id):
        ca.msgn.send_message(recipient_id, dict(speech="Please enter text "
                                                "message."))

    def handle_msg_data(self, data):
        raise NotImplementedError()

    def reply_text_message(self, app, sender_id, mevent):
        raise NotImplementedError()


def init_action(flask_app, do_action):
    flask_app.do_action = do_action
    return flask_app
