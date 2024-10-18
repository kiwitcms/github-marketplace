# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html
# pylint: disable=import-outside-toplevel
from datetime import timedelta

from django.db import migrations


def forwards(apps, schema_editor):  # pylint: disable=unused-argument
    from django.utils import timezone

    from tcms_github_marketplace import docker
    from tcms_github_marketplace import fastspring
    from tcms_github_marketplace import github
    from tcms_github_marketplace import utils

    purchase_model = apps.get_model("tcms_github_marketplace", "Purchase")
    for purchase in (
        purchase_model.objects.filter(
            action="purchased",
            received_on__gte=timezone.now() - timedelta(days=32),
        )
        .exclude(subscription=None)
        .order_by("-received_on")
    ):
        if (
            purchase.payload["marketplace_purchase"]["plan"]["monthly_price_in_cents"]
            > 0
        ):
            try:
                sku = ""
                if purchase.vendor == "fastspring":
                    sku = fastspring.find_sku(purchase)
                elif purchase.vendor == "github":
                    sku = github.find_sku(purchase)

                with docker.QuayIOAccount(purchase.subscription) as account:
                    account.create()
                    utils.configure_product_access(account, sku)
                print(f"Created new account for {purchase.subscription}@{purchase.pk}")
            except Exception as err:  # noqa, pylint: disable=broad-exception-caught
                print(f"Error for {purchase.subscription}@{purchase.pk} -> {err}")


class Migration(migrations.Migration):
    dependencies = [
        ("tcms_github_marketplace", "0010_prefix_fastspring_subscription_id"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
