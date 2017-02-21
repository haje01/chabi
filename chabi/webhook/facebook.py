"""API.AI Webhook."""
import time
import json

import requests
from flask import Blueprint, current_app as ca, request

facebook = Blueprint('facebook', __name__)


def init_facebook_app(flask_app, page_access_token, verify_token):
    flask_app.page_access_token = page_access_token
    flask_app.verify_token = verify_token
    flask_app.register_blueprint(facebook)
    return flask_app


@facebook.route('/', methods=['GET'])
def hello():
    return "OK", 200


@facebook.route('/facebook', methods=['GET'])
def verify():
    """Verify Facebook webhook registration."""
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and\
            request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") ==\
                ca.verify_token:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "OK", 200


def analyze_and_handle_message(sender_id, mevent):
    """Analyze message and handle the result by App handler.

    Note:
        `analyze_message` of ChatBot Wrapper, analyzes messages via ChatBot API.
        `handle_incomplete` of ChatBot Wrapper, handles entity filling message.
        `handle_unknown` of ChatBot Wrapper, handles unknown messages from user.
        `handle_analyzed` of App, handles result from ChatBot API.
    """
    # the message's text
    msg_text = mevent["message"]["text"]

    st = time.time()
    assert hasattr(ca, 'analyze_message')
    ca.logger.debug('analyzing start: {}'.format(msg_text))
    res = ca.analyze_message(sender_id, msg_text)
    ca.logger.debug('analyzing elapsed: {0:.2f}'.format(time.time() - st))
    if type(res) is not str:
        res = res.read()
    data = json.loads(res)

    incomplete, res = ca.handle_incomplete(data)
    if incomplete:
        ca.logger.info("incomplete message: {}".format(res))
        return res

    unknown, res = ca.handle_unknown(data)
    if unknown:
        ca.logger.info("unknown message: {}".format(res))
        return res

    st = time.time()
    assert hasattr(ca, 'handle_analyzed')
    ca.logger.debug('handling start: {}'.format(data))
    res = ca.handle_analyzed(data)
    ca.logger.debug("handled result: {}".format(res))
    ca.logger.debug('handling elapsed: {0:.2f}'.format(time.time() - st))

    return res


def _webhook_handle_page(data):
    for entry in data["entry"]:
        for messaging_event in entry["messaging"]:
            ca.logger.debug("Webhook: {}".format(messaging_event))

            # the facebook ID of the person sending you the message
            sender_id = messaging_event["sender"]["id"]
            # the recipient's ID, which should be your page's
            # facebook ID
            recipient_id = messaging_event["recipient"]["id"]  # NOQA

            # send reply action first
            send_reply_action(sender_id)

            # someone sent us a message
            if messaging_event.get("message"):
                res = analyze_and_handle_message(sender_id, messaging_event)
                send_message(sender_id, res)

            # delivery confirmation
            if messaging_event.get("delivery"):
                pass
            # optin confirmation
            if messaging_event.get("optin"):
                pass
            # user clicked/tapped "postback" button in earlier message
            if messaging_event.get("postback"):
                pass


@facebook.route('/facebook', methods=['POST'])
def webhook():
    """Webhook for Facebook message."""
    # endpoint for processing incoming messaging events
    data = request.get_json()
    if data is not None:
        ca.logger.debug("Request:")
        ca.logger.debug(json.dumps(data, indent=4))

        if 'object' in data:
            if data["object"] == "page":
                _webhook_handle_page(data)

    return "", 200


def send_reply_action(recipient_id):
    data = {
        'sender_action': 'typing_on'
    }
    _send_data(recipient_id, data)


def send_message(recipient_id, res):
    data = {
        'message': {'text': res['speech']}
    }
    #tres = type(res)
    #if tres is dict:
        #if 'data' in res:
            #if 'facebook' in res['data']:
                #fbdata = res['data']['facebook']
                #if 'attachment' in fbdata:
                    #data['attachment'] = fbdata['attachment']
                #else:
                    #data['message'] = fbdata['text']
                    #ca.logger.warning('No attachment in facebook data: {}'.format(fbdata))
            #else:
                #ca.logger.warning('No facebook data: {}'.format(res['data']))
        #else:
            #ca.logger.warning('No data in res: {}'.format(res))
    #elif tres is string:
        #data['message'] = {'text': res }

    _send_data(recipient_id, data)


def _send_data(recipient_id, data):
    ca.logger.debug("sending message to {recipient}: {data}".format(
        recipient=recipient_id, data=data))

    params = {
        "access_token": ca.page_access_token
    }
    headers = {
        "Content-Type": "application/json"
    }

    data['recipient'] = {
        "id": recipient_id
    }
    ca.logger.debug("FB _send_data: {}".format(data))
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params=params, headers=headers, data=json.dumps(data))
    if r.status_code != 200:
        ca.logger.error(r.status_code)
        ca.logger.error(r.text)
