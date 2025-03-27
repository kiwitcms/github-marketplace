# Copyright (c) 2019-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import hmac
import hashlib
from base64 import b64encode
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.translation import gettext_lazy as _

from tcms.core.utils.mailto import mailto
from tcms_github_marketplace import docker


def verify_hmac(request):
    """
    Verifies request comes from FastSpring, see:
    https://docs.fastspring.com/integrating-with-fastspring/webhooks#Webhooks-securityMessageSecret/Security
    """
    received_signature = request.headers.get("X-FS-Signature", None)
    if not received_signature:
        return HttpResponseForbidden()

    # HMAC SHA256
    payload_signature = hmac.new(
        settings.KIWI_FASTSPRING_SECRET, msg=request.body, digestmod=hashlib.sha256
    ).digest()
    # turn binary string into str !!!
    payload_signature = b64encode(payload_signature).decode()

    # due to security reasons do not use '==' operator
    # https://docs.python.org/3/library/hmac.html#hmac.compare_digest
    if not hmac.compare_digest(received_signature, payload_signature):
        return HttpResponseForbidden()

    return True  # b/c of inconsistent-return-statements


def cancel_plan(purchase):
    """
    Cancells the current plan from Marketplace:
    https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/cancelling-plans/
    """
    try:
        with docker.QuayIOAccount(purchase.subscription) as account:
            account.delete()
    except:  # noqa:E722, pylint: disable=bare-except
        pass

    # send exit poll email
    mailto(
        template_name="tcms_github_marketplace/email/exit_poll.txt",
        recipients=[purchase.sender],
        subject=str(_("Kiwi TCMS Subscription Exit Poll")),
    )

    # Note: deliberately not removing users from DB b/c this removes
    # accounts for customers with > 1 active subscription.
    # Inactive users will be removed via cron job!

    return HttpResponse("cancelled", content_type="text/plain")


def calculate_paid_until(mp_purchase, effective_date):
    """
    Calculates when access to paid services must be disabled.
    """
    paid_until = effective_date
    if mp_purchase["billing_cycle"] == "monthly":
        paid_until += timedelta(days=31)
    elif mp_purchase["billing_cycle"] == "yearly":
        paid_until += timedelta(days=366)

    # above we give them 1 extra day and here we always end at 23:59:59
    return paid_until.replace(hour=23, minute=59, second=59)


def organization_from_purchase(purchase):
    """
    Helps support organizational purchases
    """
    if purchase is None:
        return ""

    if purchase.payload["marketplace_purchase"]["account"]["type"] == "Organization":
        return purchase.payload["marketplace_purchase"]["account"]["login"]

    return ""


def configure_product_access(quay_account, sku):
    for repo_name in sku.split("+"):
        if repo_name and not repo_name.startswith("x-"):
            quay_account.allow_read_access(repo_name)
