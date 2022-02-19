# pylint: disable=import-outside-toplevel
from django.apps import AppConfig as DjangoAppConfig
from django.core.checks import register


class AppConfig(DjangoAppConfig):
    name = "tcms_github_marketplace"

    def ready(self):
        from tcms_github_marketplace import checks

        register(checks.quay_io_token)
