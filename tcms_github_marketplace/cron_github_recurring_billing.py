# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

"""
Query GitHub Marketplace b/c they don't send events for recurring billing!
"""

from datetime import timedelta

import github

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.test import RequestFactory
from django.utils import timezone

from django_tenants.utils import get_public_schema_name, schema_context
from tcms_github_marketplace.models import Purchase
from tcms_github_marketplace.views import GithubCronProcessor


def check_github_for_subscription_renewals(
    # vvv monthly subscriptions between [-29d, now] are still current
    # vvv monthly subscriptions made > 50 days ago are considered expired
    monthly_range=(
        timezone.now() - timedelta(days=50),
        timezone.now() - timedelta(days=29),
    ),
    yearly_range=(
        timezone.now() - timedelta(days=380),
        timezone.now() - timedelta(days=350),
    ),
    # ^^^ yearly subscriptions [-350d, now] are still current
    # ^^^ yearly subscriptions made > 380 days ago are considered expired
):
    anonymous_user = AnonymousUser()
    factory = RequestFactory()
    gh_app = github.GithubIntegration(
        auth=github.Auth.AppAuth(
            settings.KIWI_GITHUB_APP_ID, settings.KIWI_GITHUB_APP_PRIVATE_KEY
        ),
    )
    hub = (
        gh_app._GithubIntegration__requester  # pylint: disable=protected-access,no-member
    )
    processed = {}

    with schema_context(get_public_schema_name()):
        # Find purchases made in the last 45-29 days to be inspected.
        # Loop over most-recent records first, skipping over non unique account IDs!
        for purchase in Purchase.objects.filter(
            Q(received_on__range=monthly_range) | Q(received_on__range=yearly_range),
            action="purchased",
            vendor__startswith="github",
            payload__marketplace_purchase__plan__monthly_price_in_cents__gt=0,
        ).order_by("-received_on"):
            # this is the subscriber account
            account_id = purchase.payload["marketplace_purchase"]["account"]["id"]

            # ignore records for accounts which have been processed
            # to avoid generating duplicate events
            if processed.get(account_id, False):
                continue
            processed[account_id] = True

            # ignore accounts for which there is a newer record
            # in the DB (potentially renewed via previous cron execution or cancelled)
            # this will avoid creation of multiple DB records for the same customer
            # b/c we inspect a rolling period of 20-30 days!
            if Purchase.objects.filter(
                payload__marketplace_purchase__account__id=account_id,
                received_on__gt=monthly_range[1],
            ).exists():
                continue

            # ask GitHub Marketplace if this is still an active subscriber
            # NOTE: in day-to-day executions we may be querying this unnecessary
            try:
                _headers, response = hub.requestJsonAndCheck(
                    "GET", f"/marketplace_listing/accounts/{account_id}"
                )
            except github.UnknownObjectException:
                # usually happens when not a subscriber
                continue

            next_billing_date_from_marketplace = purchase.next_billing_date_from(
                response
            )

            if next_billing_date_from_marketplace is None:
                continue

            # Customer has been charged and we need to extend their usage
            # WARNING: b/c this code executes via cron it is possible that the record we're
            # currently looking at was generated by the same code on its previous execution!
            # If that is the case billing dates would be the same and the comparison below will
            # not trigger!
            # When the dates are different, that's how we know a subscription was renewed!
            if purchase.next_billing_date < next_billing_date_from_marketplace:
                event = {
                    "action": "purchased",
                    "effective_date": timezone.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    "sender": purchase.payload["sender"],
                    "marketplace_purchase": response["marketplace_purchase"],
                }
                event["marketplace_purchase"]["account"] = {
                    "id": response["id"],
                    "login": response["login"],
                    "organization_billing_email": response.get(
                        "organization_billing_email", response.get("email")
                    ),
                    "type": response["type"],
                    "url": response["url"],
                }

                request = factory.post(
                    "/github/cron/", data=event, content_type="application/json"
                )
                # middleware are not supported here so we simulate some fields
                request.user = anonymous_user

                response = GithubCronProcessor.as_view()(request)
                assert response.status_code == 200


if __name__ == "__main__":
    check_github_for_subscription_renewals()
