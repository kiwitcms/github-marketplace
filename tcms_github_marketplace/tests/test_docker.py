# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import unittest

from parameterized import parameterized
from tcms_github_marketplace import docker


class TestQuayIOAccount(unittest.TestCase):
    @parameterized.expand(
        [
            ("user@example.com", "user_example_com"),
            ("user+kiwi@example.com", "user_kiwi_example_com"),
            ("john-doe@my-company.com", "john_doe_my_company_com"),
        ]
    )
    def test_email_conversion_to_account_name(self, email, expected):
        account = docker.QuayIOAccount(email)
        self.assertEqual(account.name, expected)
