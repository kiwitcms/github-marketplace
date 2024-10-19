# Copyright (c) 2022-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

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
        with docker.QuayIOAccount(email) as account:
            self.assertEqual(account.name, expected)

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_username(self):
        with docker.QuayIOAccount("bob@example.com") as account:
            try:
                account.create()
                self.assertEqual(account.username, "kiwitcms+bob_example_com")
            finally:
                account.delete()

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_token(self):
        with docker.QuayIOAccount("token@example.io") as account:
            try:
                account.create()
                self.assertNotEqual(account.token, "")
            finally:
                account.delete()

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_with_subscription_id_from_fastspring(self):
        with docker.QuayIOAccount("fs-FEL1qVcbTyGEjBFRQ9FuAw") as account:
            try:
                account.create()
                self.assertEqual(account.username, "kiwitcms+fs_fel1qvcbtygejbfrq9fuaw")
                self.assertNotEqual(account.token, "")
            finally:
                account.delete()

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_with_subscription_id_from_github(self):
        with docker.QuayIOAccount("gh-44892260-31894430") as account:
            try:
                account.create()
                self.assertEqual(account.username, "kiwitcms+gh_44892260_31894430")
                self.assertNotEqual(account.token, "")
            finally:
                account.delete()

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_create_account(self):
        now = timezone.now().strftime("%Y%m%d%H%M%S")
        with docker.QuayIOAccount(f"testing-{now}-create-account") as account:
            try:
                response = account.create()
                self.assertIn("name", response)
                self.assertIn("token", response)
                self.assertEqual(response["name"], f"kiwitcms+{account.name}")

                # try a second time
                response = account.create()
                self.assertIn("Existing robot with name", response["error_message"])
            finally:
                account.delete()

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_delete_account(self):
        now = timezone.now().strftime("%Y%m%d%H%M%S")
        with docker.QuayIOAccount(f"testing-{now}-delete-account") as account:
            account.create()
            time.sleep(1)

            response = account.delete()
            self.assertEqual(response, "")

            # try a second time
            response = account.delete()
            response = json.loads(response)
            self.assertIn(
                "Could not find robot with specified username", response["message"]
            )

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_allow_read_access(self):
        now = timezone.now().strftime("%Y%m%d%H%M%S")
        with docker.QuayIOAccount(f"testing-{now}-allow-read-access") as account:
            try:
                account.create()

                for _ in range(2):
                    response = account.allow_read_access("upstream")
                    self.assertEqual(response["role"], "read")
                    self.assertEqual(response["name"], account.username)
                    self.assertEqual(response["is_robot"], True)
            finally:
                account.delete()

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_regenerate_token(self):
        now = timezone.now().strftime("%Y%m%d%H%M%S")
        with docker.QuayIOAccount(f"testing-{now}-regenerate-token") as account:
            try:
                account.create()
                first_token = account.token

                response = account.regenerate_token()
                self.assertNotEqual(account.token, first_token)
                self.assertNotEqual(response["token"], first_token)

                self.assertEqual(
                    response["token"],
                    account._token,  # pylint: disable=protected-access
                )
                self.assertEqual(
                    response["name"],
                    account._username,  # pylint: disable=protected-access
                )
            finally:
                account.delete()
