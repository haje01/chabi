"""Messenger API implementation of Facebook."""
import json

import requests
from flask import Blueprint, current_app as ca, request

from chabi import analyze_and_action
from chabi import MessengerBase

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
                results = ca.msgn.handle_msg_data(data)

    return json.dumps(results), 200


class Facebook(MessengerBase):

    def __init__(self, flask_app, page_access_token, verify_token):
        super(Facebook, self).__init__(flask_app, blueprint, page_access_token,
                                       verify_token)

    def get_text_msg(self, mevent):
        try:
            return mevent['message']['text']
        except KeyError:
            return

    def _send_data(self, recipient_id, data):
        if self.page_access_token is None:
            # Usually test case
            self.logger.warning("PAGE_ACCESS_TOKEN is None, Skip sending.")
            return

        self.logger.debug("sending message to {recipient}: {data}".format(
            recipient=recipient_id, data=data))

        params = {
            "access_token": self.page_access_token
        }
        headers = {
            "Content-Type": "application/json"
        }

        data['recipient'] = {
            "id": recipient_id
        }
        self.logger.debug("FB _send_data: {}".format(data))
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                        params=params, headers=headers, data=json.dumps(data))
        if r.status_code != 200:
            self.logger.error(r.status_code)
            self.logger.error(r.text)
        return data

    def send_message(self, recipient_id, data):
        """Send message to recipient.

        Return:
            dict: Sent Message content.
        """
        return self._send_data(recipient_id, data)

    def send_reply_action(self, recipient_id):
        data = {
            'sender_action': 'typing_on'
        }
        return self._send_data(recipient_id, data)

    def reply_text_message(self, app, sender_id, msg_text):
        """Reply user message.

        Return:
            dict: Sent message content.
        """
        msg = analyze_and_action(sender_id, msg_text)

        has_text = msg and (type(msg) is str)
        has_attach = msg and 'message' in msg and 'attachment' in\
            msg['message']
        if has_text or has_attach:
            if has_text:
                msg = dict(message=dict(text=msg))
            self.send_message(sender_id, msg)
        else:
            app.logger.warning("Fail to analyzed message: {}".format(msg_text))
            msg = dict(message=dict(text='Oops.'))
            self.send_message(sender_id, msg)
        return msg

    def handle_msg_data(self, data):
        results = []
        app = self.app
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                app.logger.debug("Webhook: {}".format(messaging_event))

                # the facebook ID of the person sending you the message
                sender_id = messaging_event["sender"]["id"]
                msg_text = self.get_text_msg(messaging_event)
                if msg_text is None:
                    res = self.ask_enter_text_msg(sender_id)
                    results.append(res)
                    continue

                # send reply action first
                self.send_reply_action(sender_id)

                # someone sent us a message
                if messaging_event.get("message"):
                    res = self.reply_text_message(app, sender_id, msg_text)
                    results.append(res)

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


def init_facebook(flask_app, access_token, verify_token):
    Facebook(flask_app, access_token, verify_token)
    return flask_app
