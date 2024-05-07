#
# Copyright (c) 2024 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

# pylint: disable=undefined-variable

if "tcms_github_marketplace.api" not in MODERNRPC_METHODS_MODULES:  # noqa: F821
    MODERNRPC_METHODS_MODULES.append("tcms_github_marketplace.api")  # noqa: F821
