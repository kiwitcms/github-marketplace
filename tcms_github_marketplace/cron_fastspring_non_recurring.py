# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

"""
Immitate recurring billing events for one-time FastSpring products:
- products designed to allow WIRE transfer option (regardless of how they were paid)
- products sold via Kiwi TCMS Partner Store (regardless of how they were paid)

In particular:
- send 'canceled' events
- send email reminders
"""

import copy
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.mail import send_mail
from django.db.models import Count
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils import timezone

from django_tenants.utils import get_public_schema_name, schema_context
from tcms_github_marketplace import utils
from tcms_github_marketplace.models import Purchase
from tcms_github_marketplace.views import (
    CronCancelFastSpringProduct,
    CronCancelFastSpringPartner,
)


def check_fastspring_for_subscription_renewals():
    anonymous_user = AnonymousUser()
    factory = RequestFactory()

    with schema_context(get_public_schema_name()):
        # Find purchases made in the last 3 years to be inspected.
        for purchase in (
            Purchase.objects.filter(
                action="purchased",
                vendor="fastspring",
                received_on__gt=timezone.now() - timedelta(3 * 366),
                payload__marketplace_purchase__plan__monthly_price_in_cents__gt=0,
            )
            .values("subscription")
            .annotate(Count("subscription"))
        ):
            # multiple 'purchased' events for the same subscription
            if purchase["subscription__count"] > 1:
                continue

            last_purchase = (
                Purchase.objects.filter(subscription=purchase["subscription"])
                .order_by("received_on")
                .last()
            )

            # recurring subscriptions which are not ready for renewal will have the
            # 'data'.'next' field in their raw payload, which represents the next billing date
            if last_purchase.payload.get("data", {}).get("next"):
                continue

            # there are other events after the latest 'purchased' event, could be
            # reminders, failed payments or cancelation without a secondary payment so
            # most likely this is a recurring billing purchase or a cancellation
            if Purchase.objects.filter(
                subscription=last_purchase.subscription,
                received_on__gt=last_purchase.received_on,
            ).exists():
                continue

            print(
                "WILL INSPECT Purchase",
                last_purchase.pk,
                last_purchase.subscription,
            )

            paid_until = utils.calculate_paid_until(
                last_purchase.payload["marketplace_purchase"],
                last_purchase.effective_date,
                last_purchase.next_billing_date,
            )

            # already expired, send 'cancel' event this subscription ID
            if timezone.now() - paid_until > timedelta(0):
                event = copy.deepcopy(last_purchase.payload)
                payload = event
                processing_view = CronCancelFastSpringProduct

                # events from Partner Store are different from direct sales
                if last_purchase.subscription.startswith("fsp-"):
                    processing_view = CronCancelFastSpringPartner

                    event["status"] = "canceled"
                    event["statusChange"] = timezone.now().strftime(
                        "%b %d, %Y, %I:%M:%S %p"
                    )
                else:
                    event["type"] = "subscription.deactivated"
                    event["created"] = int(timezone.now().timestamp() * 1000)
                    payload = {"events": [event]}

                # NOTE: bogus URL b/c we call the view directly below
                request = factory.post(
                    "/cancel/fastspring/one-time/",
                    data=payload,
                    content_type="application/json",
                )
                # middleware is not supported here so we simulate some fields
                request.user = anonymous_user

                # NOTE: these are internal views which don't verify request signature
                response = processing_view.as_view()(request)
                assert response.status_code == 200

                continue

            # payment not due in >35 days - don't remind too early
            if paid_until - timezone.now() > timedelta(days=35):
                continue

            # <=35 days to expiration. Send email reminder
            send_mail(
                "Action required: Your Kiwi TCMS subscription will expire soon",
                render_to_string(
                    "email/notify_about_subscription_expiration.txt",
                    {
                        "latest_purchase": last_purchase,
                        "expiration_date": paid_until,
                    },
                ),
                settings.DEFAULT_FROM_EMAIL,
                [last_purchase.sender],
                fail_silently=False,
            )


if __name__ == "__main__":
    check_fastspring_for_subscription_renewals()
