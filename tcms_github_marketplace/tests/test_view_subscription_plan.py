# Copyright (c) 2022-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=too-many-ancestors
import os
import unittest

from datetime import timedelta

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import tcms_tenants
from tcms_github_marketplace import docker
from tcms_github_marketplace.models import Purchase


class MockUser:  # pylint: disable=too-few-public-methods
    type = None


class ViewSubscriptionTestCase(tcms_tenants.tests.LoggedInTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("github_marketplace_plans")

    def tearDown(self):
        Purchase.objects.all().delete()
        super().tearDown()

    def assert_on_page(self, response):
        for text in (
            "You can access the following tenants",
            "You own the following tenants",
            "Transaction history",
            "Docker credentials",
            "Username",
            "Password",
        ):
            self.assertContains(response, _(text))

    def test_page_loads_without_subscription(self):
        response = self.client.get(self.url)
        self.assert_on_page(response)
        for text in (
            "You don't own any tenants",
            "Subscribe via FastSpring",
        ):
            self.assertContains(response, _(text))

    @unittest.skipUnless(
        os.getenv("QUAY_IO_TOKEN"),
        "QUAY_IO_TOKEN is not defined",
    )
    def test_page_loads_with_subscription_and_quay_account(self):
        with docker.QuayIOAccount(self.tester.email) as account:
            try:
                account.create()
                self.test_page_loads_with_subscription_without_quay_account()

                # fetch the page again, to verify the quay.io account creds are shown
                response = self.client.get(self.url)
                self.assertContains(response, account.username)
                self.assertContains(response, account.token)
            finally:
                account.delete()

    def test_page_loads_with_subscription_without_quay_account(self):
        """
        Page should not crash if for some reason the account on Quay.io was not created!
        """
        # simulate ownership
        self.tenant.owner = self.tester
        self.tenant.save()

        # simulate purchasing
        Purchase.objects.create(
            vendor="fastspring",
            action="test-purchase",
            sender=self.tester.email,
            effective_date=timezone.now(),
            payload={
                "data": {"account": {"url": "https://example.com/cancel"}},
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 2520,
                    },
                },
            },
        )

        response = self.client.get(self.url)
        self.assert_on_page(response)
        for text in (
            "You don't own any tenants",
            "Subscribe via FastSpring",
        ):
            self.assertNotContains(response, _(text))

        for text in (
            "Tenant",
            "Private Tenant",
            "Cancel",
            "Vendor",
            "mo",
        ):
            self.assertContains(response, _(text))

        # tenant URL is shown
        self.assertContains(response, f"https://{self.get_test_tenant_domain()}")
        self.assertContains(response, "https://example.com/cancel")
        self.assertContains(response, "test-purchase")
        self.assertContains(response, "fastspring")

    def test_saving_gitops_prefix_clears_cache(self):
        # simulate ownership
        self.tenant.owner = self.tester
        self.tenant.save()

        # simulate purchasing
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender=self.tester.email,
            should_have_tenant=True,
            effective_date=timezone.now() - timedelta(days=2),
            payload={
                "data": {
                    "sku": "x-tenant+version",
                    "account": {"url": "https://example.com/cancel"},
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 5000,
                    },
                },
            },
        )

        # simulate a full cache
        cache.set("testing-key", True)

        with unittest.mock.patch("github.Github.get_user") as github_get_user:
            mock_user = MockUser()
            mock_user.type = "Organization"
            github_get_user.return_value = mock_user

            response = self.client.post(
                self.url,
                data={"gitops_prefix": "https://github.com/kiwitcms"},
                follow=True,
            )

            self.assert_on_page(response)
            self.assertContains(response, "https://github.com/kiwitcms")

            purchase.refresh_from_db()
            self.assertEqual(purchase.gitops_prefix, "https://github.com/kiwitcms")

            # cache has been cleared when the form was saved
            self.assertIsNone(cache.get("testing-key"))
