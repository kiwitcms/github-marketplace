# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcms_github_marketplace", "0007_manualpurchase"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchase",
            name="gitops_prefix",
            field=models.CharField(
                blank=True, db_index=True, max_length=256, null=True
            ),
        ),
    ]
