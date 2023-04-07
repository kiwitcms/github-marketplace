# Generated by Django 4.0.2 on 2022-02-20 13:42

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
