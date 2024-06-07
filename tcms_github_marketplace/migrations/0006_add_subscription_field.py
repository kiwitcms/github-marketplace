# Copyright (c) 2022-2023 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db import migrations, models


def forwards(apps, schema_editor):  # pylint: disable=unused-argument
    purchase_model = apps.get_model("tcms_github_marketplace", "Purchase")
    for purchase in purchase_model.objects.filter(vendor="fastspring"):
        data = purchase.payload["data"]
        if "subscription" in data:
            subscription = data["subscription"]
            if isinstance(subscription, dict):
                subscription = subscription["id"]

            purchase.subscription = subscription
            purchase.save()


class Migration(migrations.Migration):
    dependencies = [
        ("tcms_github_marketplace", "0005_add_support_and_tenant_flags"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchase",
            name="subscription",
            field=models.CharField(blank=True, db_index=True, max_length=32, null=True),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
