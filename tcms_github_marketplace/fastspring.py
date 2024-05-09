#
# Copyright (c) 2024 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import json

from tcms_github_marketplace.models import Purchase


def find_sku(purchase):
    """
    FastSpring SKU can be found in several different places
    """
    # this function is also called from purchase_should_have_tenant() which
    # only passes event JSON b/c the Purchase object hasn't been created yet
    event = purchase
    if isinstance(purchase, Purchase):
        event = purchase.payload
    assert isinstance(event, dict)

    # begin looking for SKU
    if "sku" in event["data"] and event["data"]["sku"]:
        return event["data"]["sku"]

    if (
        "product" in event["data"]
        and "sku" in event["data"]["product"]
        and event["data"]["product"]["sku"]
    ):
        return event["data"]["product"]["sku"]

    if (
        "subscription" in event["data"]
        and "sku" in event["data"]["subscription"]
        and event["data"]["subscription"]["sku"]
    ):
        return event["data"]["subscription"]["sku"]

    sku = ""
    if "items" in event["data"]:
        for item in event["data"]["items"]:
            if "sku" in item:
                sku += item["sku"] or ""

        if sku:
            return sku

    if "kiwitcms-private-tenant" in json.dumps(event):
        sku = "x-tenant+version"

    if "kiwitcms-enterprise" in json.dumps(event):
        sku = "x-tenant+version+enterprise"

    return sku
