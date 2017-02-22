"""Chatbot API implementation of API.AI"""

import json

from flask import Blueprint, current_app as ca, request, make_response
import apiai as api_ai

from chabi.vendor import ChatbotAPI


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
                res = ca.uapp.do_action(data)
                action_done = True

    if not action_done:
        assert hasattr(ca.uapp, 'do_action')
        res = ca.uapp.do_action(data)

    ca.logger.debug("Response:")
    res = json.dumps(res, indent=4)
    # ca.logger.debug(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def request_analyze(sender_id, msg):
    token = ca.chatbot.api_access_token
    ai = api_ai.ApiAI(token)
    request = ai.text_request()
    request.lang = 'en'
    request.session_id = sender_id
    request.query = msg
    response = request.getresponse()
    return response


def handle_incomplete(data):
    if data['result']['actionIncomplete']:
        ff = data['result']['fulfillment']
        res = {'speech': ff['speech']}
        return True, res
    return False, None


def handle_unknown(data):
    if data['result']['action'] == 'input.unknown':
        ca.logger.debug("Unknown {}".format(data))
        ff = data['result']['fulfillment']
        res = {'speech': ff['speech']}
        return True, res
    return False, None


class ApiAI(ChatbotAPI):
    def __init__(self, flask_app, access_token):
        super(ApiAI, self).__init__(flask_app, blueprint, access_token)


def init_apiai(flask_app, access_token):
    ApiAI(flask_app, access_token)
    return flask_app


def init_user_app(flask_app, user_do_action):
    flask_app.do_action = user_do_action
    return flask_app
