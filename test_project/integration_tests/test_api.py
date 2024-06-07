# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html


# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors,attribute-defined-outside-init,no-member

import unittest

from tcms_api.xmlrpc import TCMSXmlrpc


class AnonymousRpc(TCMSXmlrpc):  # pylint: disable=too-few-public-methods
    def _do_login(self):
        pass


def anonymous_rpc_client(url):
    return AnonymousRpc(None, None, url).server


class TestGitOpsAllow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # WARNING: this is communicating directly with the container, not routed
        # through the localhost port binding!
        cls.rpc = anonymous_rpc_client("https://testing.example.bg:8443/xml-rpc/")

    def test_can_execute_rpc_method_anonymously(self):
        result = self.rpc.GitOps.allow(
            "https://github.com/atodorov/testing-with-python"
        )
        self.assertEqual(result, False)


if __name__ == "__main__":
    unittest.main()
