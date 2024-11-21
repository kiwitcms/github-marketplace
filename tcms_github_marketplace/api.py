# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=missing-permission-required, no-self-use

from django.core.cache import cache
from django.utils import timezone
from modernrpc.core import rpc_method

from tcms_github_marketplace import utils
from tcms_github_marketplace.models import Purchase


@rpc_method(name="GitOps.allow")
def gitops_allow(repo_url):  # pylint: disable=missing-api-permissions-required
    """
    .. function:: RPC GitOps.allow(repo_url)

        Whether or not ``kiwitcms/gitops`` can continue processing the given repository
        depending on the fact that there's an active subscription configured!

        :param repo_url: A URL to a repository, e.g. https://github.com/kiwitcms/Kiwi
        :type repo_url: str
        :return: ``True`` or ``False``
        :rtype: bool
    """
    key = f"gitops-allow-{repo_url}"

    result = cache.get(key)
    if result is not None:
        return result

    purchase = (
        Purchase.objects.filter(
            action="purchased",
            gitops_prefix__iprefix_for=repo_url,
            payload__marketplace_purchase__plan__monthly_price_in_cents__gt=0,
        )
        .order_by("-received_on")
        .first()
    )

    if purchase is None:
        cache.set(key, False)
        return False

    paid_until = utils.calculate_paid_until(
        purchase.payload["marketplace_purchase"],
        purchase.effective_date,
    )

    result = timezone.now() <= paid_until
    cache.set(key, result)
    return result
