# Copyright (c) 2019-2023 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tcms_github_marketplace", "0002_update_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="purchase",
            name="sender",
            field=models.EmailField(db_index=True, max_length=254),
        ),
    ]
