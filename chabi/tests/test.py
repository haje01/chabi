"""Basic tests."""
import json

import flask
from flask import Flask


def test_facebook():
    """Facebook messenger API test."""
    from chabi.messenger import init_facebook_app

    app = init_facebook_app(Flask(__name__), 'access_token', 'page_access_token')

    # default GET
    with app.test_client() as c:
        r = c.get('/webhook')
        assert 'OK' == r.data.decode('utf8')
        assert '200 OK' == r.status

    # GET with bad verify token
    with app.test_client() as c:
        r = c.get('/webhook?hub.mode=subscribe&hub.challenge=challenge_code&hub.verify_token=BAD')
        assert 'Verification token mismatch' == r.data.decode('utf8')
        assert '403 FORBIDDEN' == r.status

    # GET with good verify token
    with app.test_client() as c:
        r = c.get('/webhook?hub.mode=subscribe&hub.challenge=challenge_code&hub.verify_token=access_token')
        assert 'challenge_code' == r.data.decode('utf8')
        assert '200 OK' == r.status


    # POST to webhook
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
        c.post('/webhook', headers={'Content-Type': 'application/json'},
               data=json.dumps(data))
