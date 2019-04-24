# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from http import HTTPStatus

from django.urls import reverse
from django.http import HttpResponseForbidden
from django.test import RequestFactory, TestCase

from tcms_github_marketplace import utils


class VerifySignatureTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse('github_marketplace_purchase_hook')

    def test_missing_signature_header(self):
        request = self.factory.post(self.url)
        result = utils.verify_signature(request)

        self.assertIsInstance(result, HttpResponseForbidden)
        self.assertEqual(HTTPStatus.FORBIDDEN, result.status_code)

    def test_invalid_signature_header(self):
        request = self.factory.post(self.url)
        request.META['HTTP_X_HUB_SIGNATURE'] = 'invalid-ssh1'
        result = utils.verify_signature(request)

        self.assertIsInstance(result, HttpResponseForbidden)
        self.assertEqual(HTTPStatus.FORBIDDEN, result.status_code)
