# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors,attribute-defined-outside-init,no-member

from datetime import timedelta

from django import test
from django.core.cache import cache
from django.utils import timezone

from tcms_github_marketplace import api
from tcms_github_marketplace.models import Purchase


class TestGitOpsAllow(test.TestCase):
    # WARNING: exercising the FUT directly instead of going through the
    # XML-RPC API layer b/c of difficulties creating a multi-tenant LiveServer

    def tearDown(self):
        Purchase.objects.all().delete()
        cache.clear()
        super().tearDown()

    def test_when_no_purchase_matching_repo_then_result_is_false(self):
        result = api.gitops_allow("https://github.com/atodorov/testing-with-python")
        self.assertEqual(result, False)

    def test_when_active_purchase_with_zero_price_matching_repo_then_result_is_false(
        self,
    ):
        Purchase.objects.create(
            vendor="testing",
            action="purchased",
            gitops_prefix="https://github.com/kiwitcms",
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
        # warning: ^^^ price is 0

        result = api.gitops_allow("https://github.com/kiwitcms/enterprise")
        self.assertEqual(result, False)

    def test_when_expired_purchase_with_non_zero_price_matching_repo_then_result_is_false(
        self,
    ):
        Purchase.objects.create(
            vendor="testing",
            action="purchased",
            gitops_prefix="https://github.com/kiwitcms",
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=32),
            payload={
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 1500,
                    },
                }
            },
        )
        # warning: expired 1 day ago

        result = api.gitops_allow("https://github.com/kiwitcms/enterprise")
        self.assertEqual(result, False)

    def test_when_active_purchase_with_non_zero_price_matching_repo_then_result_is_true(
        self,
    ):
        Purchase.objects.create(
            vendor="testing",
            action="purchased",
            gitops_prefix="https://github.com/kiwitcms",
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=23),
            payload={
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 1500,
                    },
                }
            },
        )

        result = api.gitops_allow("https://github.com/kiwitcms/enterprise")
        self.assertEqual(result, True)

        result = api.gitops_allow("https://github.com/kiwitcms/tcms-api")
        self.assertEqual(result, True)

        # trying for a different repository which will not match
        result = api.gitops_allow("https://github.com/atodorov/testing-with-python")
        self.assertEqual(result, False)

    def test_when_multiple_purchase_with_non_zero_price_matching_repo_then_result_is_true(
        self,
    ):
        # already expired
        Purchase.objects.create(
            vendor="testing",
            action="purchased",
            gitops_prefix="https://github.com/kiwitcms",
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=35),
            payload={
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 1500,
                    },
                }
            },
        )

        # still active
        Purchase.objects.create(
            vendor="testing",
            action="purchased",
            gitops_prefix="https://github.com/kiwitcms",
            sender="kiwitcms-bot@example.bg",
            effective_date=timezone.now() - timedelta(days=13),
            payload={
                "marketplace_purchase": {
                    "billing_cycle": "monthly",
                    "plan": {
                        "monthly_price_in_cents": 1500,
                    },
                }
            },
        )

        result = api.gitops_allow("https://github.com/kiwitcms/enterprise")
        self.assertEqual(result, True)

        result = api.gitops_allow("https://github.com/kiwitcms/tcms-api")
        self.assertEqual(result, True)

        # trying for a different repository which will not match
        result = api.gitops_allow("https://github.com/atodorov/testing-with-python")
        self.assertEqual(result, False)
