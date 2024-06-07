# Copyright (c) 2023 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=too-many-ancestors, too-many-lines
from unittest.mock import call, patch

from django.urls import reverse
from parameterized import parameterized

import tcms_tenants

from tcms_github_marketplace import docker
from tcms_github_marketplace import mailchimp
from tcms_github_marketplace.models import Purchase


class ProcessManualPurchaseTestCase(tcms_tenants.tests.LoggedInTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # the Manual Purchase Add form is available only to super-user
        cls.tester.is_superuser = True
        cls.tester.save()

    @parameterized.expand(["monthly", "yearly"])
    def test_initial_subscription(self, billing_cycle):
        form_data = {
            "invoice": "TEST-2023-04-14",
            "price": "4800",
            "billing_cycle": billing_cycle,
            "customer_name": "Testing Department",
            "address": "Bulgaria",
            "billing_email": "billing@example.com",
            "technical_email": "devops@example.com",
            "sku": "x-tenant+version+enterprise",
        }

        initial_purchase_count = Purchase.objects.count()
        self.assertFalse(
            Purchase.objects.filter(
                vendor="manual_purchase",
                action="purchased",
                sender="devops@example.com",
            ).exists()
        )

        # tmp_account calculates the actual robot name for mocking - currently not in use
        with docker.QuayIOAccount(self.tester.email) as tmp_account:
            with patch.object(
                docker.QuayIOAccount,
                "create",
                return_value={"name": tmp_account.name, "token": "secret"},
            ) as quay_io_create, patch.object(
                docker.QuayIOAccount,
                "allow_read_access",
                return_value="success",
            ) as quay_io_allow_read_access, patch.object(
                mailchimp,
                "subscribe",
                return_value="success",
            ) as mailchimp_subscribe, patch(
                "tcms_github_marketplace.views.mailto"
            ) as fulfillment_email:
                response = self.client.post(
                    reverse("admin:tcms_github_marketplace_manualpurchase_add"),
                    form_data,
                    follow=True,
                )
                self.assertRedirects(
                    response,
                    reverse("admin:tcms_github_marketplace_purchase_changelist"),
                )
                self.assertContains(response, form_data["invoice"])
                self.assertContains(response, form_data["price"])

                quay_io_create.assert_called_once()
                quay_io_allow_read_access.assert_has_calls(
                    [call("version"), call("enterprise")], any_order=True
                )
                mailchimp_subscribe.assert_called_once_with("devops@example.com")
                fulfillment_email.assert_called_once_with(
                    template_name="email/manual_subscription_notification.txt",
                    recipients=["billing@example.com", "devops@example.com"],
                    subject="Kiwi TCMS subscription notification",
                    context={},
                )
        self.assertEqual(initial_purchase_count + 1, Purchase.objects.count())
        purchase = Purchase.objects.filter(
            vendor="manual_purchase",
            action="purchased",
            sender="devops@example.com",
            should_have_tenant=True,
        ).first()

        self.assertIsNotNone(purchase)
        self.assertEqual(
            purchase.payload["marketplace_purchase"]["billing_cycle"], billing_cycle
        )
        self.assertEqual(
            purchase.payload["data"]["customer_name"], form_data["customer_name"]
        )
        # this is an initial subscription so Tenant hasn't been created yet The used needs
        # to do this by visiting the Create Tenant page
        self.assertFalse(
            tcms_tenants.models.Tenant.objects.filter(
                owner__email="devops@example.com"
            ).exists()
        )
