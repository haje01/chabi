"""Basic tests."""
import json

from flask import Flask


def test_apiai():
    """API.AI webhook test."""
    from chabi.webhook import init_apiai_app

    def process_request(data):
        return dict(processed=data['foo'])

    app = init_apiai_app(Flask(__name__), process_request)

    with app.test_client() as c:
        r = c.get('/apiai')
        assert '200 OK' == r.status

    data = dict(foo=123)

    with app.test_client() as c:
        r = c.post('/apiai', headers={'Content-Type': 'application/json'},
               data=json.dumps(data))
        assert '200 OK' == r.status
        assert 'processed' in r.data.decode('utf8')


def foo():
    CLIENT_ACCESS_TOKEN = 'c38cd18726d5470cb848daf2c41d9a8a'
    import apiai
    api = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
    request = api.text_request()
    request.lang = 'en'
    request.session_id = 'ukn_session_id'
    request.query = "how's weather of korea?"
    response = request.getresponse()
    import pdb; pdb.set_trace()  # XXX BREAKPOINT
    print(response.read())


def test_facebook():
    """Facebook webhook test."""
    from chabi.webhook import init_facebook_app

    app = init_facebook_app(Flask(__name__), 'access_token',
                            'verify_token')

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
