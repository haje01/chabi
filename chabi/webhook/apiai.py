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


def init_apiai_app(flask_app, api_access_token, process_message):
    flask_app.register_blueprint(apiai)

    assert not hasattr(flask_app, 'api_access_token')
    flask_app.api_access_token = api_access_token
    assert not hasattr(flask_app, 'analyze_message')
    flask_app.analyze_message = analyze_message
    assert not hasattr(flask_app, 'process_message')
    flask_app.process_message = process_message
    assert not hasattr(flask_app, 'handle_incomplete')
    flask_app.handle_incomplete = handle_incomplete

    return flask_app


@apiai.route('/apiai', methods=['GET', 'POST'])
def webhook():
    # ca.logger.debug(request.args)
    if request.method == 'GET':
        return 'OK', 200

    data = request.get_json(silent=True, force=True)
    # ca.logger.debug("Request:")
    # ca.logger.debug(json.dumps(data, indent=4))

    assert hasattr(ca, 'process_message')
    res = ca.process_message(data)

    ca.logger.debug("Response:")
    res = json.dumps(res, indent=4)
    # ca.logger.debug(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r
