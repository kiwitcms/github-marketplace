#!/usr/bin/env python
# pylint: disable=missing-docstring

# Copyright (c) 2019-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import os
import sys

if __name__ == "__main__":
    if os.path.exists("kiwitcms_github_marketplace.egg-info"):
        print("ERORR: .egg-info/ directories mess up plugin loading code in devel mode")
        sys.exit(1)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_project.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
