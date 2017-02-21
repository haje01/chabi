import time
import json

from flask import current_app as ca


def analyze_and_action(sender_id, mevent):
    """Analyze message and do action for the result.

    Note:
        `analyze_message` of ChatBot Wrapper, analyzes messages via ChatBot
            API.
        `handle_incomplete` of ChatBot Wrapper, handles entity filling message.
        `handle_unknown` of ChatBot Wrapper, handles unknown messages from
            user.
        `do_action` of App, do action for analyzed result from ChatBot API.

    Returns:
        dict: Handled or action result (contains return message)
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

    hresult = None
    assert hasattr(ca, 'handle_incomplete')
    assert hasattr(ca, 'handle_unknown')
    assert hasattr(ca, 'do_action')

    # check entity filling
    incomplete, res = ca.handle_incomplete(data)
    if incomplete:
        ca.logger.info("incomplete message: {}".format(res))
        hresult = res

    # check unknown message
    if hresult is None:
        unknown, res = ca.handle_unknown(data)
        if unknown:
            ca.logger.info("unknown message: {}".format(res))
            hresult = res

    # check action needs to be done
    if hresult is None:
        st = time.time()
        if len(data['result']['action']) > 0:
            action = data['result']['action']
            ca.logger.debug("action '{}' start: {}".format(action, data))
            res = ca.do_action(data)
            ca.logger.debug("action result: {}".format(res))
            ca.logger.debug('action elapsed: {0:.2f}'.format(time.time() - st))
            hresult = res

    # normal reply
    if hresult is None:
        hresult = data['result']['fulfillment']

    return hresult
