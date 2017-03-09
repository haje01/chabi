"""Messenger API implementation of Facebook."""
import json

import requests
from flask import Blueprint, current_app as ca, request, render_template,\
    redirect, make_response
from pony import orm

from chabi import analyze_and_action, action_by_analyzed,\
    make_chatbot_session_id
from chabi import MessengerBase, EventHandlerBase as _EventHandlerBase
from chabi.models import AccountLink

blueprint = Blueprint('facebook', __name__,
                      template_folder='templates',
                      static_folder='static',
                      static_url_path='/static/facebook')


def account_link_template(image_url, login_url):
    """Return account link template for Facebook."""
    data =  render_template('facebook/account_link.json', image_url=image_url,
                            login_url=login_url)
    return json.loads(data)


def account_unlink_template(login_image_url):
    """Return account unlink template for Facebook."""
    data = render_template('facebook/account_unlink.json',
                           image_url=login_image_url)
    return json.loads(data)


def postback_button_template(text, buttons):
    data = render_template('facebook/buttons.json', text=text, buttons=buttons)
    return json.loads(data)


def quick_reply_template(text, items):
    replies = []
    for name, payload in items:
        reply = {
            "content_type": "text",
            "title": name,
            "payload": payload
        }
        replies.append(reply)

    return {
        "message": {
            "text": text,
            "quick_replies": replies
        }
    }


def get_logged_account_link(target_id):
    al = orm.select(a for a in AccountLink if a.id == target_id)[:]
    if len(al) > 0:
        return al[0]


class EventHandlerBase(_EventHandlerBase):
    def __init__(self, app, start_msg="", login_image_url="", login_url=""):
        """Init event handler.

        Args:
            app: Flask app instan:ce.
            start_msg (optin): Start message when start button was pressed.
            login_image_url (optional): Login image URL for login template.
            login_url (optional): Login URL to where login request is directed.
        """
        super(EventHandlerBase, self).__init__(app)
        self.start_msg = start_msg
        self.login_image_url = login_image_url
        self.login_url = login_url

    def confirm_intent(self, sender_id, confirm_msg, confirm_action):
        """Confirm intent by quick reply."""
        yesno = [
            ('Yes', 'yes.' + confirm_action),
            ('no', 'no.' + confirm_action),
        ]
        return quick_reply_template(confirm_msg, yesno)

    def trigger_account_event(self, sender_id, payload):
        alink = get_logged_account_link(sender_id)
        if alink is None:
            return render_template('facebook/need_login.txt')

        event = payload.split('.')[1]
        cb_session_id = make_chatbot_session_id(sender_id, ca)
        res = self.app.chatbot.trigger_event(cb_session_id, event)
        data = res.read()
        data = json.loads(data)
        return action_by_analyzed(sender_id, data)

    def handle_quick_reply(self, sender_id, text, payload):
        """Handle Facebook common quick reply.

        Returns:
            dict or str: Result text message.
        """
        if payload.startswith('no.'):
            return "OK. Please tell me about it more specifically."
        elif payload.startswith('yes.'):
            return self.trigger_account_event(sender_id, payload)

    def handle_action(self, sender_id, data):
        """Handle common action for Facebook event.

        Args:
            sender_id: Message sender id.
            data: Message data.

        Returns:
            dict: Response data
        """
        action = data.get("result").get("action")

        if action == "login":
            if get_logged_account_link(sender_id):
                return "You are already logged in."
            return self.handle_action_login(sender_id)
        elif action == 'logout':
            if not get_logged_account_link(sender_id):
                return "You are not logged in."
            return self.handle_action_logout(sender_id)

    def handle_action_login(self, target_id):
        """Handle login action.

        Note:
            login_image_url, login_url must have valid value.
        """
        assert len(self.login_image_url) > 0
        assert len(self.login_url) > 0
        return account_link_template(self.login_image_url, self.login_url)

    def handle_action_logout(self, target_id):
        """Handle logout action.

        Note:
            login_image_url, login_url must have valid value.
        """
        assert len(self.login_image_url) > 0
        assert len(self.login_url) > 0
        return account_unlink_template(self.login_image_url)


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
            return render_template('facebook/login.html', service=service,
                                   error=error)
        else:
            # send auth ok to facebook
            ca.logger.warning("User {} logged in".format(user))
            redirect_uri = request.cookies.get('redirect_uri')
            ruri = '{}&authorization_code={}'.format(redirect_uri, auth_code)
            return redirect(ruri)
    else:
        # GET
        redirect_uri = request.args.get('redirect_uri')
        html = render_template('facebook/login.html', service=service,
                               error=error)
        res = make_response(html)
        res.set_cookie('redirect_uri', redirect_uri)
        return res


@blueprint.route('/facebook', methods=['POST'])
def webhook():
    """Endpoint for processing incoming messaging events."""
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


def get_quickreply_payload(mevent):
    try:
        return mevent['message']['quick_reply']['payload']
    except KeyError:
        return


def get_text_msg(mevent):
    try:
        return mevent['message']['text']
    except KeyError:
        return


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

    def _send_data(self, recipient_id, data):
        if len(data) == 0:
            return data

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

        Args:
            data(str or dict): Message data to send.

        Return:
            dict: Sent Message content.
        """
        data_is_str = type(data) is str
        if data_is_str:
            data = dict(message=dict(text=data))
        return self._send_data(recipient_id, data)

    def send_reply_action(self, recipient_id):
        data = {
            'sender_action': 'typing_on'
        }
        return self._send_data(recipient_id, data)

    def handle_text_message(self, sender_id, msg_text):
        """Reply to user message.

        Build reply message by analyzing user message via Chatbot API, then
        send it.

        Args:
            sender_id: Message sender id.
            msg_text: Received text message.

        Return:
            dict or str: Sent message content.
        """
        reply = analyze_and_action(sender_id, msg_text)
        if not reply:
            self.logger.warning("Fail to analyze message: {}".format(msg_text))
            reply = "Oops."

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
            if res is not None:
                self.send_message(sender_id, res)
                results.append(res)
                return True

        # account linking(login)
        if mevent.get("account_linking"):
            linked = mevent['account_linking']['status']
            if linked == 'unlinked':
                self.logger.warning("recipient {} has unlinked "
                                    .format(recipient_id))
                res = self.handle_account_unlink(sender_id)
            else:
                self.logger.warning("recipient {} has linked "
                                    .format(recipient_id))
                auth_code = mevent['account_linking']['authorization_code']
                res = self.handle_account_link(sender_id, auth_code)

            self.send_message(sender_id, res)
            results.append(res)
            return True

        msg_text = get_text_msg(mevent)
        if msg_text is None:
            res = self.ask_enter_text_msg(sender_id)
            results.append(res)
            return True

        # someone sent us a message
        if mevent.get("message"):
            qr_payload = get_quickreply_payload(mevent)
            if qr_payload is not None:
                # handle quick reply
                res = self.app.evth.handle_quick_reply(sender_id, msg_text,
                                                       qr_payload)
            else:
                # handle text message
                res = self.handle_text_message(sender_id, msg_text)

            if res:
                self.send_message(sender_id, res)
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

    def handle_account_link(self, sender_id, auth_code):
        """Handle account link message event.

        Create DB account link object, then return message.

        Args:
            sender_id: messenger user id
            auth_code: Auth code to Facebook message check.

        Returns:
            dict: Structured result message.
        """
        if get_logged_account_link(sender_id):
            return "You are already logged in."
        AccountLink(id=sender_id, auth_code=auth_code)

        return "You have successfully logged in."

    def handle_account_unlink(self, sender_id):
        """Handle account unlink message event.

        Delete DB account link object, then return message.

        Args:
            sender_id: messenger user id

        Returns:
            dict: Structured result message.
        """
        al = get_logged_account_link(sender_id)
        if not al:
            return "You are not logged in."

        al.delete()
        return "You have successfully logged out."
