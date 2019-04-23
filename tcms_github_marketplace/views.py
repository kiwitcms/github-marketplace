# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import json

from django.views.generic.base import TemplateView

from tcms_github_marketplace import utils


class PurchaseHook(TemplateView):
    """
        Handles `marketplace_purchase` web hook as described at:
        https://developer.github.com/marketplace/listing-on-github-marketplace/configuring-the-github-marketplace-webhook/
    """
    def post(self, request, *args, **kwargs):
        """
            Hook must be configured to receive JSON payload!
        """
        utils.verify_signature(request)

        payload = json.loads(request.POST)

        if payload['action'] == 'purchased':
            utils.handle_purchased(payload)
        elif payload['action'] == 'cancelled':
            utils.handle_cancelled(payload)

        raise NotImplementedError(
            'Unsupported GitHub Marketplace hook action %s' %
            payload['action'])
