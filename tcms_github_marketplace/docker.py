# Copyright (c) 2022-2024 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.conf import settings
from .quay import QuayApiClient


class QuayIOAccount:
    organization = "kiwitcms"

    def __init__(self, subscription_id):
        self._api = None
        self._subscription = subscription_id
        self._token = None
        self._username = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._api:
            self._api.session.session.close()

    @property
    def api(self):
        """
        Initialize API client only when needed
        """
        if not self._api:
            self._api = QuayApiClient(token=settings.QUAY_IO_TOKEN)

        return self._api

    @property
    def name(self):
        """
        Transform a subscription ID or email address to a valid robot account name for Quay.io
        """
        return (
            self._subscription.replace("@", "_")
            .replace(".", "_")
            .replace("+", "_")
            .replace("-", "_")
            .lower()
        )

    @property
    def username(self):
        if not self._username:
            self._update_token_and_username()
        return self._username

    @property
    def token(self):
        if not self._token:
            self._update_token_and_username()
        return self._token

    def _update_token_and_username(self, response=None):
        if not response:
            response = self.api.get_robot_from_organization(
                self.name, self.organization
            )

        if response:
            self._token = response.get("token")
            self._username = response.get("name")

    def create(self):
        """
        Will create a robot account if it doesn't exist. Will not crash if a
        robot account with this name already exists.
        """
        return self.api.create_robot_in_organization(self.name, self.organization)

    def delete(self):
        """
        Note: if response is not empty string then it's a JSON string containing error
        message. Currently we don't handle this!
        """
        return self.api.delete_robot_from_organization(self.name, self.organization)

    def allow_read_access(self, repo_name):
        repository = f"{self.organization}/{repo_name}"
        return self.api.update_user_permissions(self.username, repository, role="read")

    def regenerate_token(self):
        response = self.api.regenerate_robot_token(self.name, self.organization)
        self._update_token_and_username(response)
        return response
