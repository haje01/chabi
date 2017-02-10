"""Messenger Server Adapters."""


class Server(object):
    """Base server."""

    def __init__(self, api):
        """Init."""
        self.api = api


class CLI(Server):
    """CLI Server."""

    pass


class Web(Server):
    """Web Server."""

    pass


class Facebook(Server):
    """Adapter for Facebook messenger."""

    pass
