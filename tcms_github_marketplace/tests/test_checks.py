# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors

from django.core.checks import Error
from django.test import override_settings

from tcms_tenants.tests import LoggedInTestCase
from tcms_github_marketplace import checks


class QuayIOTokenCheckTestCase(LoggedInTestCase):
    def test_check_passes_when_setting_is_set(self):
        self.assertEqual(checks.quay_io_token(None), [])

    @override_settings(QUAY_IO_TOKEN=None)
    def test_check_fails_when_env_var_is_not_set(self):
        expected_errors = [
            Error(
                msg="settings.QUAY_IO_TOKEN is not defined!",
                hint=("This variable is mandatory"),
            ),
        ]
        self.assertEqual(checks.quay_io_token(None), expected_errors)
