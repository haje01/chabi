"""Chatbot API implementation of API.AI"""
import time
import json

from flask import Blueprint, current_app as ca, request, make_response
import apiai as api_ai

from chabi import ChatbotBase


blueprint = Blueprint('apiai', __name__)


@blueprint.route('/apiai', methods=['GET', 'POST'])
def webhook():
    """"Webhook for API.AI.

    Note:
        This end point is for direct request from API.AI(development phase).
        Not from real messenger requests. Messengers have their own end point,
        where requests to API.AI are made by ApiAI request method.

    """
    if request.method == 'GET':
        return 'OK', 200

    data = request.get_json(silent=True, force=True)

    action_done = False
    if 'result' in data:
        if 'action' in data['result']:
            if data['result']['action'] == 'input.unknown':
                res = data['result']['fullfillment']
                res = ca.evth.handle_action(data)
                action_done = True

    if not action_done:
        res = ca.evth.handle_action(data)

    ca.logger.debug("Response:")
    res = json.dumps(res, indent=4)
    # ca.logger.debug(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


class ApiAI(ChatbotBase):
    def __init__(self, app, access_token):
        """Init ApiAI Instance.

        Args:
            app: Flask app instance.
            access_token: API.AI client access token.
        """
        super(ApiAI, self).__init__(app, blueprint, access_token)

    def request_analyze(self, sender_id, msg):
        token = self.access_token
        ai = api_ai.ApiAI(token)
        request = ai.text_request()
        request.lang = 'en'
        request.session_id = sender_id
        request.query = msg
        response = request.getresponse()
        return response

    def handle_action(self, data):
        """Handle action to be done.

        Args:
            data: Result json data from API.AI

        Returns:
            boolean: True if action executed False otherwise.
            str: Result message after action.
        """
        st = time.time()
        result = data['result']
        action = result['action']
        if action and 'actionIncomplete' in result and\
                not result['actionIncomplete']:
            ca.logger.debug("action '{}' start: {}".format(action, data))
            res = ca.evth.handle_action(data)
            if res:
                ca.logger.debug("action result: {}".format(res))
                ca.logger.debug('action elapsed: {0:.2f}'.format(time.time() -
                                                                 st))
                return True, res
        return False, None

    def handle_incomplete(self, data):
        """Handle incomplete action(usually fi entity filling).

        Returns:
            boolean: Whether action incomplete or not.
            str: Entity filling question when action incomplete.
        """
        result = data['result']
        if 'actionIncomplete' in result and result['actionIncomplete']:
            return True, self.extract_text_msg(data)
        return False, None

    def handle_unknown(self, data):
        """Handle unknown action.

        Returns:
            boolean: Whether unknown action or not.
            str: Question when unknown action occurred.
        """
        result = data['result']
        if 'action' in result and result['action'] == 'input.unknown':
            self.logger.debug("Unknown {}".format(data))
            return True, self.extract_text_msg(data)
        return False, None

    def extract_text_msg(self, data):
        result = data['result']
        if 'fulfillment' in result and result['fulfillment']:
            return result['fulfillment']['speech']
