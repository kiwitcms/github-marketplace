# pylint: disable=avoid-auto-field
# Generated by Django 4.1.7 on 2023-04-09 20:42

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
