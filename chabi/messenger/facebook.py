"""API.AI server."""

import json

import requests
from flask import Blueprint, current_app, request


facebook = Blueprint('handler', __name__)


@facebook.route('/webhook', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and\
            request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") ==\
                current_app.verify_token:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "OK", 200


@facebook.route('/webhook', methods=['POST'])
def webhook():
    # endpoint for processing incoming messaging events
    data = request.get_json()
    print(data)

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                # someone sent us a message
                if messaging_event.get("message"):

                    # the facebook ID of the person sending you the message
                    sender_id = messaging_event["sender"]["id"]
                    # the recipient's ID, which should be your page's
                    # facebook ID
                    recipient_id = messaging_event["recipient"]["id"]
                    # the message's text
                    message_text = messaging_event["message"]["text"]
                    print("sender {}, recipient {}, message "
                          "{}".format(sender_id, recipient_id, message_text))

                    send_message(sender_id, "got it, thanks!")

                # delivery confirmation
                if messaging_event.get("delivery"):
                    pass
                # optin confirmation
                if messaging_event.get("optin"):
                    pass
                # user clicked/tapped "postback" button in earlier message
                if messaging_event.get("postback"):
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    print("sending message to {recipient}: "
          "{text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": current_app.page_access_token
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)


def init_facebook_app(flask_app, verify_token, page_access_token):
    flask_app.verify_token = verify_token
    flask_app.page_access_token = page_access_token
    flask_app.register_blueprint(facebook)
    return flask_app
