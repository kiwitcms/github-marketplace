# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors
import os
import unittest

from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import tcms_tenants
from tcms_github_marketplace import docker
from tcms_github_marketplace.models import Purchase


class ViewSubscriptionTestCase(tcms_tenants.tests.LoggedInTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("github_marketplace_plans")

    def tearDown(self):
        Purchase.objects.all().delete()

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
