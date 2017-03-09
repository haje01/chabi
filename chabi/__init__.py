import time
import json
from datetime import datetime

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

    Args:
        sender_id: Message sender id.
        msg_text: Message text.

    Returns:
        str: Result text message.
    """
    st = time.time()
    ca.logger.debug('analyzing start: {}'.format(msg_text))
    cb_session_id = make_chatbot_session_id(sender_id, ca)
    res = ca.chatbot.request_analyze(cb_session_id, msg_text)
    ca.logger.debug('analyzing elapsed: {0:.2f}'.format(time.time() - st))
    if res is None:
        return

    if type(res) is not str:
        res = res.read()
    data = json.loads(res)
    return action_by_analyzed(sender_id, data)


def action_by_analyzed(sender_id, data):
    """Do action based on response from Chatbot.

    Args:
        sender_id: Message sender id.
        data: Analyzed data from Chatbot.

    Returns:
        str: Result text message.
    """
    # check unknown message
    unknown, res = ca.chatbot.handle_unknown(data)
    if unknown:
        ca.logger.info("unknown message: {}".format(res))
        return res

    # check action needs to be done
    action_done, res = ca.chatbot.handle_action(sender_id, data)
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

    def __init__(self, app, blueprint):
        """Init chatbot base.

        Args:
            app: A Flask app instance.
            blueprint: Flask blueprint for url routing.
        """
        super(ChatbotBase, self).__init__(app)
        app.chatbot = self
        app.register_blueprint(blueprint)
        app.cb_start_dt = datetime.fromtimestamp(time.time())

    def request_analyze(self, session_id, msg):
        """Request text analysis by Chatbot API.

        Args:
            session_id: ApiAI Session ID. Made of sender_id + app start time.
            msg: Text to analyze.

        Returns:
            str or HTTP Stream: Analyzed result in JSON format.
        """
        raise NotImplementedError()

    def handle_action(self, sender_id, data):
        """Handle action to be done.

        Resolve Chatbot API specific data, delegate them to
        EventHandler.

        Args:
            sender_id: Message sender id.
            data: Result json data from API.AI

        Returns:
            boolean: True if action executed False otherwise.
            str: Result message after action.
        """
        raise NotImplementedError()

    def handle_unknown(self):
        """Handle unknown action.

        Returns:
            boolean: Whether unknown action or not.
            str: Question when unknown action occurred.
        """
        raise NotImplementedError()

    def handle_incomplete(self):
        """Handle incomplete action(usually for entity filling).

        Returns:
            boolean: Whether action incomplete or not.
            str: Entity filling question when action incomplete.
        """
        raise NotImplementedError()

    def extract_text_msg(self, data):
        """Extract text message from payload."""
        raise NotImplementedError()

    def trigger_event(self, session_id, event):
        """Trigger Chatbot event to proceed next intent.

        Args:
            session_id: Chatbot Session ID. Made of sender_id + app start time.
            event_name: Name of event.

        Returns:
            str or HTTP Stream: Analyzed result in JSON format.
        """
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

    def handle_text_message(self, app, sender_id, mevent):
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
        """Handle postback event.

        Args:
            msg: Message data.

        Returns:
            str: Response message.
        """
        raise NotImplementedError()

    def handle_quick_reply(self, sender_id, text, payload):
        raise NotImplementedError()

    def confirm_intent(self, sender_id, confirm_msg, confirm_action):
        raise NotImplementedError()


def make_chatbot_session_id(msgn_id, app):
    """Make chatbot session ID from messenger ID and app start time.

    Args:
        msgn_id: Messenger user ID
        app: Flask app instance (has start time attribute).
    Returns:
    """
    fmt = '%Y-%m-%d %H:%M:%S'
    return "{}_{}".format(msgn_id, app.cb_start_dt.strftime(fmt))
