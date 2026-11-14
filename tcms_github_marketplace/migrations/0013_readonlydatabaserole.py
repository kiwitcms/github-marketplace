# pylint: disable=avoid-auto-field
#
# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcms_github_marketplace", "0012_privaterepotoken"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReadOnlyDatabaseRole",
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
                ("name", models.CharField(db_index=True, max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("valid_until", models.DateTimeField(db_index=True)),
                ("password", models.CharField(max_length=36)),
            ],
        ),
    ]
