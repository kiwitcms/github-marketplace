# Copyright (c) 2024 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt


# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors

from django import test
from django.utils import timezone

from tcms_github_marketplace.models import Purchase


class TestIPrefixForLookup(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # NOTE: will use the `action` field as value placeholder
        # and the `sender` field as something to assert against
        Purchase.objects.create(
            vendor="testing",
            action="https://github.com/kiwitcms",
            sender="kiwitcms-bot@example.com",
            effective_date=timezone.now(),
            payload={
                "monthly_price_in_cents": 0,
            },
        )

        Purchase.objects.create(
            vendor="testing",
            action="https://GitLab.com/kiwitcms",
            sender="atodorov@example.com",
            effective_date=timezone.now(),
            payload={
                "monthly_price_in_cents": 0,
            },
        )

        Purchase.objects.create(
            vendor="testing",
            action="https://gitlab.com/KiwiTcms",
            sender="atodorov@example.bg",
            effective_date=timezone.now(),
            payload={
                "monthly_price_in_cents": 0,
            },
        )

        Purchase.objects.create(
            vendor="testing",
            action="https://git.kiwitcms.org",
            sender="private@example.com",
            effective_date=timezone.now(),
            payload={
                "monthly_price_in_cents": 0,
            },
        )

    def test_filtering_works(self):
        for value in [
            "https://github.com/kiwitcms/Kiwi",
            "https://github.com/kiwitcms/enterprise",
        ]:
            query = Purchase.objects.filter(action__iprefix_for=value)
            self.assertEqual(query.count(), 1)

            purchase = query.first()
            self.assertIsNotNone(purchase)
            self.assertEqual(purchase.sender, "kiwitcms-bot@example.com")

        query = Purchase.objects.filter(
            action__iprefix_for="https://gitlab.com/kiwitcms/Hello-World"
        )
        self.assertEqual(query.count(), 2)

        for purchase in query:
            self.assertIsNotNone(purchase)
            self.assertTrue(purchase.sender.startswith("atodorov"))

        query = Purchase.objects.filter(action__iprefix_for="https://git")
        self.assertEqual(query.count(), 0)

        query = Purchase.objects.filter(action__iprefix_for="git")
        self.assertEqual(query.count(), 0)

        query = Purchase.objects.filter(
            action__iprefix_for="https://git.example.bg/something"
        )
        self.assertEqual(query.count(), 0)
