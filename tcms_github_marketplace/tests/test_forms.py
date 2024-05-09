# Copyright (c) 2024 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt


# -*- coding: utf-8 -*-

from datetime import timedelta
from mock import patch

from django import test
from django.utils import timezone

from tcms_github_marketplace import forms
from tcms_github_marketplace.models import Purchase


class MockUser:  # pylint: disable=too-few-public-methods
    type = None


class TestUpdateGitopsPrefixForm(test.TestCase):
    # exercise form validation and assert on the various error conditions

    def tearDown(self):
        Purchase.objects.all().delete()
        super().tearDown()

    def test_value_should_not_be_empty(self):
        form = forms.UpdateGitopsPrefixForm({"gitops_prefix": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("Value cannot be empty", form.errors["gitops_prefix"])

    def test_value_should_start_with_http(self):
        form = forms.UpdateGitopsPrefixForm({"gitops_prefix": "ftp://example.com"})
        self.assertFalse(form.is_valid())
        self.assertIn("Value is not a URL", form.errors["gitops_prefix"])

        form = forms.UpdateGitopsPrefixForm({"gitops_prefix": "git.example.com"})
        self.assertFalse(form.is_valid())
        self.assertIn("Value is not a URL", form.errors["gitops_prefix"])

    def test_subscription_is_required(self):
        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/is-none"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Subscription required", form.errors["gitops_prefix"])

    def test_should_not_be_able_to_change_existing_prefix(self):
        purchase = Purchase.objects.create(
            vendor="github",
            action="purchased",
            gitops_prefix="https://github.com/atodorov",
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 0,
                    },
                }
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/kiwitcms/"}, instance=purchase
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Cannot change existing prefix. Contact Support",
            form.errors["gitops_prefix"],
        )

    def test_subscription_with_unknown_vendor_should_fail_to_validate(self):
        purchase = Purchase.objects.create(
            vendor="testing",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 0,
                    },
                }
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/kiwitcms/"}, instance=purchase
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Unknown vendor. Contact Support", form.errors["gitops_prefix"])

    def test_should_not_be_able_to_change_prefix_for_subscription_via_github(self):
        purchase = Purchase.objects.create(
            vendor="github",
            action="purchased",
            # WARNING: this shouldn't happen in reality b/c the value is filled-in automatically
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 0,
                    },
                }
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/kiwitcms/"}, instance=purchase
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Prefix for GitHub subscription cannot be configured manually",
            form.errors["gitops_prefix"],
        )

    def test_for_subscription_via_fastspring_should_fail_when_sku_not_found(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {},
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 40000,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/kiwitcms/"}, instance=purchase
        )
        self.assertFalse(form.is_valid())
        self.assertIn("SKU not found", form.errors["gitops_prefix"])

    def test_fastspring_enterprise_should_not_accept_bare_github_com_url(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {
                    "sku": "x-tenant+version+enterprise",
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 40000,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/"}, instance=purchase
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Bare https://github.com prefix not allowed", form.errors["gitops_prefix"]
        )

    def test_fastspring_enterprise_should_accept_any_other_url(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {
                    "sku": "x-tenant+version+enterprise",
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 40000,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://git.example.bg"}, instance=purchase
        )
        self.assertTrue(form.is_valid())

    def test_fastspring_private_tenant_should_accept_only_github_com_urls(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {
                    "sku": "x-tenant+version",
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 5000,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://example.com/owner/repo"}, instance=purchase
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Only https://github.com/ prefix allowed", form.errors["gitops_prefix"]
        )

    def test_fastspring_self_support_should_accept_only_github_com_urls(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {
                    "sku": "version",
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 1500,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://example.com/owner/repo"}, instance=purchase
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Only https://github.com/ prefix allowed", form.errors["gitops_prefix"]
        )

    def test_fastspring_should_not_validate_when_api_requests_to_github_fail(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {
                    "sku": "x-tenant+version",
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 5000,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/kiwitcms"}, instance=purchase
        )

        # WARNING: settings.KIWI_GITHUB_PAT_FOR_CHECKING_ORGS_AND_USERNAMES is invalid
        # during local development and testing and will cause authentication to fail!
        self.assertFalse(form.is_valid())
        self.assertIn("API request to GitHub failed", form.errors["gitops_prefix"])

    def test_fastspring_should_not_validate_when_username_not_found(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {
                    "sku": "x-tenant+version",
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 5000,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/kiwitcms"}, instance=purchase
        )

        with patch("github.Github.get_user") as github_get_user:
            import github  # pylint: disable=import-outside-toplevel

            github_get_user.side_effect = github.UnknownObjectException(
                404, {"message": "not found"}, {}
            )

            self.assertFalse(form.is_valid())
            self.assertIn(
                "User or Organization not found", form.errors["gitops_prefix"]
            )

    def test_fastspring_private_tenant_can_use_organizational_repositories(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            should_have_tenant=True,
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {
                    "sku": "x-tenant+version",
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 5000,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/kiwitcms"}, instance=purchase
        )

        with patch("github.Github.get_user") as github_get_user:
            mock_user = MockUser()
            mock_user.type = "Organization"
            github_get_user.return_value = mock_user

            self.assertTrue(form.is_valid())

    def test_fastspring_private_tenant_can_use_personal_repositories(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            should_have_tenant=True,
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {
                    "sku": "x-tenant+version",
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 5000,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/atodorov"}, instance=purchase
        )

        with patch("github.Github.get_user") as github_get_user:
            mock_user = MockUser()
            mock_user.type = "User"
            github_get_user.return_value = mock_user

            self.assertTrue(form.is_valid())

    def test_fastspring_self_support_cannot_use_organizational_repositories(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            should_have_tenant=False,
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {
                    "sku": "version",
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 1500,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/kiwitcms"}, instance=purchase
        )

        with patch("github.Github.get_user") as github_get_user:
            mock_user = MockUser()
            mock_user.type = "Organization"
            github_get_user.return_value = mock_user

            self.assertFalse(form.is_valid())
            self.assertIn(
                "Self-Support subscribers cannot configure Organizational repositories",
                form.errors["gitops_prefix"],
            )

    def test_fastspring_self_support_can_use_personal_repositories(self):
        purchase = Purchase.objects.create(
            vendor="fastspring",
            action="purchased",
            gitops_prefix=None,
            sender="kiwitcms-bot@example.bg",
            should_have_tenant=False,
            effective_date=timezone.now() - timedelta(days=25),
            payload={
                "data": {
                    "sku": "version",
                },
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 1500,
                    },
                },
            },
        )

        form = forms.UpdateGitopsPrefixForm(
            {"gitops_prefix": "https://github.com/atodorov"}, instance=purchase
        )

        with patch("github.Github.get_user") as github_get_user:
            mock_user = MockUser()
            mock_user.type = "User"
            github_get_user.return_value = mock_user

            self.assertTrue(form.is_valid())
