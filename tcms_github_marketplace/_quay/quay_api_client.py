import logging

from .quay_session import QuaySession

LOG = logging.getLogger("pubtools.quay")


class QuayApiClient:
    """Class for performing Quay REST API queries."""

    def __init__(self, token, host=None):
        """
        Initialize.

        Args:
            token (str):
                Quay API token for authentication.
            host (str):
                Quay registry URL.
        """
        self.token = token
        self.session = QuaySession(hostname=host, api="quay")
        self.session.set_auth_token(self.token)
