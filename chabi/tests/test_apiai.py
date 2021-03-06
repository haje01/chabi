"""Basic tests."""
import os
import json
import random
import string

from flask import Flask
import pytest
import apiai

from chabi import EventHandlerBase
from chabi.vendor.apiai import ApiAI


@pytest.fixture
def sess():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _
                   in range(20))


def apiai_text_request(sess_id, text):
    access_token = os.environ.get('APIAI_API_ACCESS_TOKEN')
    assert access_token is not None

    api = apiai.ApiAI(access_token)
    request = api.text_request()
    request.lang = 'en'
    request.session_id = sess_id
    request.query = text
    res = request.getresponse()
    return json.loads(res.read())


#
# Note:
#    To test API.AI, You need to build an Pizza Agent by importing
#    chabi/chabi/tests/prjs/apiai/PizzaAgent.zip. Then copy client access
#    token of the Agent and set APIAI_API_ACCESS_TOKEN environment
#    variable before run pytest
#
#        $ APIAI_API_ACCESS_TOKEN=CLIENT-ACCESS-TOKEN py.test -k\
#        >test_apiai
#


def test_apiai_api(sess):
    """API.AI API Test."""
    res = apiai_text_request(sess, "hello")
# {
#     'id': '4692c77c-9eb7-4423-ae9e-4848787dca44',
#     'timestamp': '2017-02-20T10:26:31.226Z',
#     'lang': 'en',
#     'result': {
#         'source': 'agent',
#         'resolvedQuery': 'hello',
#         'action': 'input.welcome',
#         'actionIncomplete': False,
#         'parameters': {},
#         'contexts': [],
#         'metadata': {
#             'intentId': 'b9bd4b96-91da-4a00-bc7b-bad1abb818a1',
#             'webhookUsed': 'false',
#             'webhookForSlotFillingUsed': 'false',
#             'intentName': 'Default Welcome Intent'
#         },
#         'fulfillment': {
#             'speech': 'Hello!',
#             'messages': [{
#                 'type': 0,
#                 'speech': 'Hello!'
#             }]
#         },
#         'score': 1.0
#     },
#     'status': {
#         'code': 200,
#         'errorType': 'success'
#     },
#     'sessionId': 'S6T6N03EE9BJRM2Q0KRR'
# }
    status = res['status']
    assert status['code'] == 200
    result = res['result']
    assert result['actionIncomplete'] is False
    assert result['action'] == 'input.welcome'
    metadata = result['metadata']
    assert metadata['intentName'] == 'Default Welcome Intent'
    # NOTE: metadata value is not evaludated
    assert metadata['webhookUsed'] == 'false'
    fulfillment = result['fulfillment']
    assert 'speech' in fulfillment

    res = apiai_text_request(sess, "I need small pizza.")
# {
#     'id': 'b48f994e-9ca8-42d9-ac49-ec0869f08dc5',
#     'timestamp': '2017-02-20T10:29:12.992Z',
#     'lang': 'en',
#     'result': {
#         'source': 'agent',
#         'resolvedQuery': 'I need small pizza.',
#         'action': '',
#         'actionIncomplete': True,
#         'parameters': {
#             'number': '',
#             'Size': 'small',
#             'Topping': ''
#         },
#         'contexts': [{
#             'name': '23f79a8c-4384-47a1-ad95-787f5a26fb99_id_dialog_context',
#             'parameters': {
#                 'number': '',
#                 'Topping': '',
#                 'Size.original': 'small',
#                 'Size': 'small',
#                 'number.original': '',
#                 'Topping.original': ''
#             },
#             'lifespan': 2
#         }, {
#             'name': 'order_dialog_context',
#             'parameters': {
#                 'number': '',
#                 'Topping': '',
#                 'Size.original': 'small',
#                 'Size': 'small',
#                 'number.original': '',
#                 'Topping.original': ''
#             },
#             'lifespan': 2
#         }, {
#             'name': 'order_dialog_params_topping',
#             'parameters': {
#                 'number': '',
#                 'Topping': '',
#                 'Size.original': 'small',
#                 'Size': 'small',
#                 'number.original': '',
#                 'Topping.original': ''
#             },
#             'lifespan': 1
#         }],
#         'metadata': {
#             'intentId': '23f79a8c-4384-47a1-ad95-787f5a26fb99',
#             'webhookUsed': 'false',
#             'webhookForSlotFillingUsed': 'false',
#             'intentName': 'Order'
#         },
#         'fulfillment': {
#             'speech': 'What is the Topping?',
#             'messages': [{
#                 'type': 0,
#                 'speech': 'What is the Topping?'
#             }]
#         },
#         'score': 1.0
#     },
#     'status': {
#         'code': 200,
#         'errorType': 'success'
#     },
#     'sessionId': '56JM873N9X7M4V9R6G96'
# }
    result = res['result']
    assert result['actionIncomplete'] is True
    metadata = result['metadata']
    assert metadata['intentName'] == 'Order'
    params = result['parameters']
    assert params['Size'] == 'small'
    assert params['Topping'] == ''
    assert params['number'] == ''
    fulfillment = result['fulfillment']
    assert fulfillment['speech'] == 'What is the Topping?'

    res = apiai_text_request(sess, "Cheese")
    result = res['result']
    assert result['actionIncomplete'] is True
    params = result['parameters']
    assert params['Topping'] == 'cheese'
    fulfillment = result['fulfillment']
    assert fulfillment['speech'] == 'What is the number?'

    res = apiai_text_request(sess, "Two")
# {
#     'id': '260f8bff-f39f-4801-b433-f45917688547',
#     'timestamp': '2017-02-20T10:36:00.258Z',
#     'lang': 'en',
#     'result': {
#         'source': 'agent',
#         'resolvedQuery': 'Two',
#         'action': '',
#         'actionIncomplete': False,
#         'parameters': {
#             'number': '2',
#             'Size': 'small',
#             'Topping': 'cheese'
#         },
#         'contexts': [],
#         'metadata': {
#             'intentId': '23f79a8c-4384-47a1-ad95-787f5a26fb99',
#             'webhookUsed': 'false',
#             'webhookForSlotFillingUsed': 'false',
#             'intentName': 'Order'
#         },
#         'fulfillment': {
#             'speech': 'Ok, 2 small cheese Pizzas(s) confirmed!',
#             'messages': [{
#                 'type': 0,
#                 'speech': 'Ok, 2 small cheese Pizzas(s) confirmed!'
#             }]
#         },
#         'score': 1.0
#     },
#     'status': {
#         'code': 200,
#         'errorType': 'success'
#     },
#     'sessionId': 'JJ959T5ESGOWWD944LFD'
# }
    result = res['result']
    assert result['actionIncomplete'] is False
    params = result['parameters']
    assert params['number'] == '2'
    fulfillment = result['fulfillment']
    assert fulfillment['speech'] == 'Ok, 2 small cheese Pizzas(s) confirmed!'


def test_apiai_webhook(sess):
    """API.AI App test."""
    access_token = os.environ.get('APIAI_API_ACCESS_TOKEN')
    assert access_token is not None

    class EventHandler(EventHandlerBase):
        def handle_action(self, data):
            return dict(result=data['foo'])

    app = Flask(__name__)
    ApiAI(app, access_token)
    EventHandler(app)
    app.config['TESTING'] = True

    with app.test_client() as c:
        r = c.get('/apiai')
        assert '200 OK' == r.status

    data = dict(foo=123)
    with app.test_client() as c:
        r = c.post('/apiai', headers={'Content-Type': 'application/json'},
                   data=json.dumps(data))
        assert '200 OK' == r.status
        assert 'result' in r.data.decode('utf8')
