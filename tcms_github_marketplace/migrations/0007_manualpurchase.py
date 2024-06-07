# pylint: disable=avoid-auto-field

# Copyright (c) 2023 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tcms_github_marketplace", "0006_add_subscription_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="ManualPurchase",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
        ),
    ]
