# Copyright (c) 2020-2023 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tcms_github_marketplace", "0003_sender_email_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="purchase",
            name="payload",
            field=models.JSONField(),
        ),
    ]
