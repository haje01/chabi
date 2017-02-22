"""Messenger API implementation of Facebook."""
import json

import requests
from flask import Blueprint, current_app as ca, request

from chabi import analyze_and_action
from chabi.vendor import MessengerAPI

blueprint = Blueprint('facebook', __name__)


@blueprint.route('/', methods=['GET'])
def hello():
    return "OK", 200


@blueprint.route('/facebook', methods=['GET'])
def verify():
    """Verify Facebook webhook registration."""
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and\
            request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") ==\
                ca.msgn.verify_token:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "OK", 200


@blueprint.route('/facebook', methods=['POST'])
def webhook():
    """Webhook for Facebook message."""
    # endpoint for processing incoming messaging events
    data = request.get_json()
    results = None
    if data is not None:
        ca.logger.debug("Request:")
        ca.logger.debug(json.dumps(data, indent=4))

        if 'object' in data:
            if data["object"] == "page":
                results = _webhook_handle_page(data)

    return json.dumps(results), 200


def _webhook_handle_page(data):
    results = []
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
                res = analyze_and_action(sender_id, messaging_event)
                results.append(res)
                if res is not None:
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
    return results


def send_data(recipient_id, data):
    if ca.msgn.page_access_token is None:
        # Usually test case
        ca.logger.warning("PAGE_ACCESS_TOKEN is None, Skip sending.")
        return

    ca.logger.debug("sending message to {recipient}: {data}".format(
        recipient=recipient_id, data=data))

    params = {
        "access_token": ca.msgn.page_access_token
    }
    headers = {
        "Content-Type": "application/json"
    }

    data['recipient'] = {
        "id": recipient_id
    }
    ca.logger.debug("FB send_data: {}".format(data))
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params=params, headers=headers, data=json.dumps(data))
    if r.status_code != 200:
        ca.logger.error(r.status_code)
        ca.logger.error(r.text)


def send_reply_action(recipient_id):
    data = {
        'sender_action': 'typing_on'
    }
    send_data(recipient_id, data)


def send_message(recipient_id, res):
    data = {
        'message': {'text': res['speech']}
    }
    send_data(recipient_id, data)


class Facebook(MessengerAPI):

    def __init__(self, flask_app, page_access_token, verify_token):
        super(Facebook, self).__init__(flask_app, blueprint, page_access_token,
                                       verify_token)


def init_facebook(flask_app, access_token, verify_token):
    Facebook(flask_app, access_token, verify_token)
    return flask_app
