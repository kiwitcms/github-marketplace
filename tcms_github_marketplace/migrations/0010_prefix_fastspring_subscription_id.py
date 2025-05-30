# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db import migrations


def forwards(apps, schema_editor):  # pylint: disable=unused-argument
    purchase_model = apps.get_model("tcms_github_marketplace", "Purchase")
    for purchase in purchase_model.objects.filter(vendor="fastspring").exclude(
        subscription=None
    ):
        try:
            if not purchase.subscription.startswith("fs-"):
                purchase.subscription = f"fs-{purchase.subscription}"
                purchase.save()
        except:  # noqa, pylint: disable=bare-except
            pass


def backwards(apps, schema_editor):  # pylint: disable=unused-argument
    purchase_model = apps.get_model("tcms_github_marketplace", "Purchase")
    for purchase in purchase_model.objects.filter(vendor="fastspring"):
        try:
            purchase.subscription = purchase.subscription.lstrip("fs-")
            purchase.save()
        except:  # noqa, pylint: disable=bare-except
            pass


class Migration(migrations.Migration):
    dependencies = [
        ("tcms_github_marketplace", "0009_github_subscription_id"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
