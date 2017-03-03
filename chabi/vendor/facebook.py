"""Messenger API implementation of Facebook."""
import json

import requests
from flask import Blueprint, current_app as ca, request, render_template,\
    redirect, make_response

from chabi import analyze_and_action
from chabi import MessengerBase

blueprint = Blueprint('facebook', __name__, template_folder='templates',
                      static_folder='static',
                      static_url_path='/static/facebook')


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


@blueprint.route('/facebook/login', methods=['GET', 'POST'])
def login():
    service = ca.config['SERVICE']
    error = None
    auth_code = ca.config['ACCOUNT_LINK_AUTH_CODE']

    if request.method == 'POST':
        user = request.form['username']

        if user != 'haje01':
            error = "Invalid Username"
        elif request.form['password'] != 'asdf':
            error = "Invalid Password"

        if error:
            return render_template('login.html', service=service, error=error)
        else:
            # send auth ok to facebook
            ca.logger.warning("User {} logged in".format(user))
            redirect_uri = request.cookies.get('redirect_uri')
            ruri = '{}&authorization_code={}'.format(redirect_uri, auth_code)
            return redirect(ruri)
    else:
        # GET
        redirect_uri = request.args.get('redirect_uri')
        html = render_template('login.html', service=service, error=error)
        res = make_response(html)
        res.set_cookie('redirect_uri', redirect_uri)
        return res


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

    if ca.config['TESTING']:
        res = json.dumps(results)
    else:
        res = 'OK'

    return res, 200


class Facebook(MessengerBase):

    def __init__(self, app, page_access_token, verify_token):
        """Init Facebook instance.

        Args:
            app: A Flask app instance.
            page_access_token: Facebook page access token.
            verify_token: Facebook page verify token.
        """
        super(Facebook, self).__init__(app, blueprint, page_access_token,
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
                          params=params, headers=headers,
                          data=json.dumps(data))
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

    def reply_text_message(self, sender_id, msg_text):
        """Reply to user message.

        Dispatch proper reply message by analyzing user message via Chatbot
        API, then send it.

        Return:
            dict or str: Sent message content.
        """
        reply = analyze_and_action(sender_id, msg_text)
        if not reply:
            self.logger.warning("Fail to analyze message: {}".format(msg_text))
            reply = "Oops."

        reply_is_str = type(reply) is str
        if reply_is_str:
            reply = dict(message=dict(text=reply))
        self.send_message(sender_id, reply)
        return reply

    def _handle_msg_event(self, mevent, results):
        """Handle each messaging event within payload.

        Args:
            event: Messaging event to handle.
            results: List for storing this result.

        Returns:
            boolean: True to call `continue` from loop
        """
        # the facebook ID of the person sending you the message
        sender_id = mevent["sender"]["id"]
        recipient_id = mevent["recipient"]
        # send reply action first
        self.send_reply_action(sender_id)

        # handle postback
        if mevent.get("postback"):
            res = self.app.evth.handle_postback(mevent['postback'])
            self.send_message(sender_id, res)
            results.append(res)
            return True

        # account linking(login)
        if mevent.get("account_linking"):
            linked = mevent['account_linking']['status']
            if linked == 'unlinked':
                self.logger.warning("recipient {} has unlinked "
                                    .format(recipient_id))
                res = self.app.msgn.handle_account_unlink()
            else:
                self.logger.warning("recipient {} has linked "
                                    .format(recipient_id))
                auth_code = mevent['account_linking']\
                                        ['authorization_code']
                res = self.app.msgn.handle_account_link(auth_code)

            self.send_message(sender_id, res)
            results.append(res)
            return True

        msg_text = self.get_text_msg(mevent)
        if msg_text is None:
            res = self.ask_enter_text_msg(sender_id)
            results.append(res)
            return True

        # someone sent us a message
        if mevent.get("message"):
            res = self.reply_text_message(sender_id, msg_text)
            results.append(res)
            return True

        # delivery confirmation
        if mevent.get("delivery"):
            pass
        # optin confirmation
        if mevent.get("optin"):
            pass
        # user clicked/tapped "postback" button in earlier message
        if mevent.get("postback"):
            pass

    def handle_msg_data(self, data):
        """Entry for handling message payload from Facebook.

        Args:
            data: JSON data from messenger.

        Returns:
            list: Results from handling each messaging event in Facebook
                payload.
        """
        results = []
        app = self.app
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                app.logger.debug("Webhook: {}".format(messaging_event))
                cont = self._handle_msg_event(messaging_event, results)
                if cont:
                    continue
        return results

    def handle_account_link(self, code):
        return dict(message=dict(text='You have successfully logged in.'))

    def handle_account_unlink(self):
        return dict(message=dict(text='You have successfully logged out.'))
