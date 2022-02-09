# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
import os
import json
import time
import unittest

from django.utils import timezone
from parameterized import parameterized
from tcms_github_marketplace import docker


class TestQuayIOAccount(unittest.TestCase):
    def setUp(self):
        # don't be too fast when contacting quay.io
        time.sleep(2)

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

    def test_username(self):
        account = docker.QuayIOAccount("bob@example.com")
        self.assertEqual(account.username, "kiwitcms+bob_example_com")

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_create_account(self):
        try:
            now = timezone.now().strftime("%Y%m%d%H%M%S")
            account = docker.QuayIOAccount(f"testing-{now}@example.com")

            response = account.create()
            self.assertIn("name", response)
            self.assertIn("token", response)
            self.assertEqual(response["name"], f"kiwitcms+{account.name}")

            # try a second time
            response = account.create()
            self.assertIn("Existing robot with name", response["message"])
        finally:
            account.delete()

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_delete_account(self):
        now = timezone.now().strftime("%Y%m%d%H%M%S")
        account = docker.QuayIOAccount(f"testing-{now}@example.del")

        response = account.delete()
        self.assertEqual(response, "")

        # try a second time
        response = account.delete()
        response = json.loads(response)
        self.assertIn("Could not find robot with username", response["message"])

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_allow_read_access(self):
        try:
            now = timezone.now().strftime("%Y%m%d%H%M%S")
            account = docker.QuayIOAccount(f"testing-{now}@example.com")
            account.create()

            for _ in range(2):
                response = account.allow_read_access("kiwi")
                self.assertEqual(response["role"], "read")
                self.assertEqual(response["name"], account.username)
                self.assertEqual(response["is_robot"], True)
        finally:
            account.delete()
