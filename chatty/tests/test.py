"""Basic tests."""


def test_basic():
    """Basic test."""
    from chatty.server import CLI
    from chatty.api import APIAI
    api = APIAI()
    svr = CLI(api)



