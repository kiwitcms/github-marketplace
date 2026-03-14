# pylint: disable=avoid-auto-field
#
# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import django.contrib.postgres.indexes
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcms_github_marketplace", "0011_quay_accounts"),
    ]

    operations = [
        migrations.CreateModel(
            name="PrivateRepoToken",
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
                ("vendor", models.CharField(db_index=True, max_length=16)),
                (
                    "subscription",
                    models.CharField(
                        blank=True, db_index=True, max_length=32, null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("payload", models.JSONField()),
            ],
        ),
        migrations.AddIndex(
            model_name="privaterepotoken",
            index=django.contrib.postgres.indexes.GinIndex(
                fastupdate=False, fields=["payload"], name="ghmp_privaterepotoken_gin"
            ),
        ),
    ]
