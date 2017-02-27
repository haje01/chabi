"""Basic tests."""
import json

from flask import Flask
import pytest

from chabi.vendor.facebook import init_facebook
from chabi.vendor.dummy import init_dummy_chatbot


@pytest.fixture()
def app():
    ap = init_facebook(Flask(__name__), 'access_token', 'verify_token')
    ap = init_dummy_chatbot(ap, 'cb_access_token')
    ap.config['TESTING'] = True
    return ap


def test_facebook_basic(app):
    with app.test_client() as c:
        sender_id = "1265395423496458"
        msg = app.msgn.ask_enter_text_msg(sender_id)
        assert msg['speech'] == 'Please enter text message.'


def test_facebook_webhook(app):
    """Facebook webhook test."""
    # default GET
    with app.test_client() as c:
        r = c.get('/facebook')
        assert 'OK' == r.data.decode('utf8')
        assert '200 OK' == r.status

    # GET with bad verify token
    with app.test_client() as c:
        r = c.get('/facebook?hub.mode=subscribe&hub.challenge=access_token'
                  '&hub.verify_token=BAD')
        assert 'Verification token mismatch' == r.data.decode('utf8')
        assert '403 FORBIDDEN' == r.status

    # GET with good verify token
    with app.test_client() as c:
        r = c.get('/facebook?hub.mode=subscribe&hub.challenge=access_token'
                  '&hub.verify_token=verify_token')
        assert 'access_token' == r.data.decode('utf8')
        assert '200 OK' == r.status

    # POST to facebook webhook
    with app.test_client() as c:
        data = {
            'object': 'page',
            'entry': [
                {
                    'messaging': [
                        {
                            'sender': {
                                'id': 'sender_id'
                            },
                            'recipient': {
                                'id': 'recipient_id'
                            },
                            'message': {
                                'text': 'message_text'
                            }
                        }
                    ]
                }
            ]
        }
        r = c.post('/facebook', headers={'Content-Type': 'application/json'},
                   data=json.dumps(data))
        assert '200 OK' == r.status


def test_facebook_illegal(app):
    with app.test_client() as c:
        data = {
            "object": "page",
            "entry": [
                {
                    "id": "229226554209857",
                    "time": 1488160039739,
                    "messaging": [
                        {
                            "sender": {
                                "id": "1265395423496458"
                            },
                            "recipient": {
                                "id": "229226554209857"
                            },
                            "timestamp": 1488160039657,
                            "message": {
                                "mid": "mid.1488160039657:1d4b8ac609",
                                "seq": 58863,
                                "attachments": [
                                    {
                                        "type": "image",
                                        "payload": {
                                            "url": "https://scontent.xx.fbcdn.net/v/t34.0-12/16997218_1543730039000857_2025028651_n.gif?_nc_ad=z-m&oh=f1a2953fb8c25dfd56661e62ffc72435&oe=58B5BCE2"  # NOQA
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        r = c.post('/facebook', headers={'Content-Type': 'application/json'},
                   data=json.dumps(data))
        assert '200 OK' == r.status
