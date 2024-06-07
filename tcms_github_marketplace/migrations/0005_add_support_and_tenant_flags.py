# Copyright (c) 2022-2023 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tcms_github_marketplace", "0004_models_jsonfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchase",
            name="should_have_support",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="purchase",
            name="should_have_tenant",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
