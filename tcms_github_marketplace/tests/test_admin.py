# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors

from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponseForbidden

from tcms_tenants.tests import LoggedInTestCase
from tcms_github_marketplace.models import Purchase


class PurchaseAdminTestCase(LoggedInTestCase):
    def tearDown(self):
        self.tester.is_superuser = False
        self.tester.save()

    def test_changelist_unauthorized_for_regular_user(self):
        response = self.client.get(
            reverse("admin:tcms_github_marketplace_purchase_changelist")
        )
        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertIn(
            "Unauthorized", str(response.content, encoding=settings.DEFAULT_CHARSET)
        )

    def test_changelist_authorized_for_superuser(self):
        # create an object so we can use its values to validate
        # the changelist view
        purchase = Purchase.objects.create(
            vendor="test-suite",
            action="test-admin-changelist-view",
            sender=self.tester.username,
            effective_date=timezone.now(),
            payload={
                "marketplace_purchase": {
                    "plan": {
                        "monthly_price_in_cents": 2520,
                    }
                }
            },
        )

        self.tester.is_superuser = True
        self.tester.save()

        response = self.client.get(
            reverse("admin:tcms_github_marketplace_purchase_changelist")
        )

        # assert all columns that must be visible
        self.assertContains(response, purchase.pk)
        self.assertContains(response, purchase.vendor)
        # shows price column
        self.assertContains(response, "Price $/mo")
        self.assertContains(response, "25")
        self.assertContains(response, purchase.action)
        self.assertContains(response, purchase.sender)
        # timestamps are formatted according to localization
        self.assertContains(response, "Effective date")
        self.assertContains(response, "Received on")

    def test_add_not_possible(self):
        response = self.client.get(
            reverse("admin:tcms_github_marketplace_purchase_add")
        )
        self.assertRedirects(
            response,
            reverse("admin:tcms_github_marketplace_purchase_changelist"),
            fetch_redirect_response=False,
        )

    def test_delete_not_possible(self):
        # create an object so we can use its PK to resolve the
        # delete view, otherwise Django will tell us that we are trying
        # to delete a non-existing object
        purchase = Purchase.objects.create(
            vendor="test-suite",
            action="test-admin-delete-view",
            sender=self.tester.username,
            effective_date=timezone.now(),
            payload={
                "marketplace_purchase": {
                    "plan": {
                        "monthly_price_in_cents": 2520,
                    }
                }
            },
        )

        response = self.client.get(
            reverse("admin:tcms_github_marketplace_purchase_delete", args=[purchase.pk])
        )
        self.assertRedirects(
            response,
            reverse("admin:tcms_github_marketplace_purchase_changelist"),
            fetch_redirect_response=False,
        )
