# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db import migrations


def forwards(apps, schema_editor):  # pylint: disable=unused-argument
    purchase_model = apps.get_model("tcms_github_marketplace", "Purchase")
    for purchase in purchase_model.objects.filter(vendor="github", subscription=None):
        try:
            sender_id = purchase.payload["sender"]["id"]
            account_id = purchase.payload["marketplace_purchase"]["account"]["id"]

            purchase.subscription = f"gh-{sender_id}-{account_id}"
            purchase.save()
        except:  # noqa, pylint: disable=bare-except
            pass


def backwards(apps, schema_editor):  # pylint: disable=unused-argument
    purchase_model = apps.get_model("tcms_github_marketplace", "Purchase")
    purchase_model.objects.filter(  # pylint: disable=objects-update-used
        vendor="github"
    ).update(subscription=None)


class Migration(migrations.Migration):
    dependencies = [
        ("tcms_github_marketplace", "0008_add_gitops_prefix"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
