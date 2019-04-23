# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import json
import hmac
import hashlib

from django.conf import settings
from django.http import HttpResponseForbidden
from django.views.generic.base import TemplateView

from tcms_github_marketplace import utils


class PurchaseHook(TemplateView):
    """
        Handles `marketplace_purchase` web hook as described at:
        https://developer.github.com/marketplace/listing-on-github-marketplace/configuring-the-github-marketplace-webhook/
    """
    def verify_signature(self, request):
        """
            Verifies request comes from GitHub, see:
            https://developer.github.com/webhooks/securing/
        """
        signature = request.META.get('HTTP_X_HUB_SIGNATURE', None)
        if not signature:
            return HttpResponseForbidden()

        expected = 'sha1=' + hmac.new(settings.KIWI_GITHUB_MARKETPLACE_SECRET,
                                      msg=request.POST,
                                      digestmod=hashlib.sha1).hex()

        if not hmac.compare_digest(signature, expected):
            return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        """
            Hook must be configured to receive JSON payload!
        """
        self.verify_signature(request)

        payload = json.loads(request.POST)

        if payload['action'] == 'purchased':
            utils.handle_purchased(payload)
        elif payload['action'] == 'cancelled':
            utils.handle_cancelled(payload)

        raise NotImplementedError('Unsupported GitHub Marketplace hook action %s' % payload['action'])
