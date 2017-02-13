"""Basic tests."""


def test_basic():
    """Basic test."""
    from chafi.messenger import Facebook
    from chafi.api import ApiAI
    from chafi import Server
    api = ApiAI()
    msg = Facebook()
    svr = Server(api, msg)
