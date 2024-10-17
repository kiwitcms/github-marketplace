# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html


def find_sku(purchase):
    """
    GitHub Marketplace doesn't support specifying product SKUs. We could rely on the
    marketplace listing ID but we've chosen to specify the list of private Docker
    repositories inside one of the description items!
    """
    sku = ""
    for item in purchase.payload["marketplace_purchase"]["plan"]["bullets"]:
        if "Docker repositories" in item:
            sku = (
                item.replace("Docker repositories:", "")
                .replace(" ", "")
                .replace("https://", "")
                .replace("quay.io/kiwitcms/", "")
                .replace(",", "+")
            )

    return sku
