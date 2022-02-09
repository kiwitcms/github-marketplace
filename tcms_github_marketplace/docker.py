# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt


class QuayIOAccount:
    def __init__(self, email):
        self._email = email

    @property
    def name(self):
        """
        Transform an email address to a valid robot account name for Quay.io
        """
        return (
            self._email.replace("@", "_")
            .replace(".", "_")
            .replace("+", "_")
            .replace("-", "_")
        )

    @property
    def token(self):
        raise NotImplementedError

    def create(self):
        raise NotImplementedError

    def assign_permissions(self):
        raise NotImplementedError

    def regenerate_token(self):
        raise NotImplementedError
