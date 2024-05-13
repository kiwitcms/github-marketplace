# Copyright (c) 2024 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt


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
