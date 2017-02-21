"""Webhook for API.AI"""

import json

from flask import Blueprint, current_app as ca, request, make_response
import apiai as api_ai


apiai = Blueprint('apiai', __name__)


def analyze_message(sender_id, msg):
    # ca.logger.debug("analyze_message: sender_id {}".format(sender_id))
    assert hasattr(ca, 'api_access_token')
    token = ca.api_access_token
    ai = api_ai.ApiAI(token)
    request = ai.text_request()
    request.lang = 'en'
    request.session_id = sender_id
    request.query = msg
    response = request.getresponse()
    # ca.logger.debug("  message: {}".format(request))
    # ca.logger.debug("  response: {}".format(response))
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


def init_apiai_app(flask_app, api_access_token, do_action):
    flask_app.register_blueprint(apiai)

    assert not hasattr(flask_app, 'api_access_token')
    flask_app.api_access_token = api_access_token
    assert not hasattr(flask_app, 'analyze_message')
    flask_app.analyze_message = analyze_message
    assert not hasattr(flask_app, 'handle_incomplete')
    flask_app.handle_incomplete = handle_incomplete
    assert not hasattr(flask_app, 'handle_unknown')
    flask_app.handle_unknown = handle_unknown
    assert not hasattr(flask_app, 'do_action')
    flask_app.do_action = do_action

    return flask_app


@apiai.route('/apiai', methods=['GET', 'POST'])
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
                res = ca.do_action(data)
                action_done = True

    if not action_done:
        assert hasattr(ca, 'do_action')
        res = ca.do_action(data)

    ca.logger.debug("Response:")
    res = json.dumps(res, indent=4)
    # ca.logger.debug(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r
