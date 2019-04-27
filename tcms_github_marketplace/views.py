# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import json
from datetime import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from tcms_github_marketplace import utils
from tcms_github_marketplace.models import Purchase


class PurchaseHook(View):
    """
        Handles `marketplace_purchase` web hook as described at:
        https://developer.github.com/marketplace/listing-on-github-marketplace/configuring-the-github-marketplace-webhook/
    """
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        """
            Hook must be configured to receive JSON payload!

            Save the 'purchased' event in the database, see:
            https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/github-marketplace-webhook-events/
        """
        result = utils.verify_signature(request)
        if result is not True:
            return result  # must be an HttpResponse then

        payload = json.loads(request.body.decode('utf-8'))

        # ping hook https://developer.github.com/webhooks/#ping-event
        if 'zen' in payload:
            return HttpResponse('pong', content_type='text/plain')

        # format is 2017-10-25T00:00:00+00:00
        effective_date = datetime.strptime(payload['effective_date'][:19],
                                           '%Y-%m-%dT%H:%M:%S')
        # save payload for future use
        purchase = Purchase.objects.create(
            action=payload['action'],
            sender=payload['sender']['login'],
            effective_date=effective_date,
            marketplace_purchase=payload['marketplace_purchase'],
        )

        # plan cancellations must be handled here
        if purchase.action == 'cancelled':
            return utils.cancel_plan(purchase)

        return HttpResponse('ok', content_type='text/plain')


@method_decorator(login_required, name='dispatch')
class Install(View):
    """
        Handles application "installation", see:
        https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/handling-new-purchases-and-free-trials/

        1) User makes an initial purchase and GitHub sends marketplace_purchase hook
           which is handled in PurchaseHook view and the payload is stored in DB.
        2) GitHub will then redirect to the Installation URL which is this view.
        3) Because we are an OAuth app begin the authorization flow as soon as
           GitHub redirects the customer to the Installation URL.

           NOTE: this is achieved by @login_required and configuring the
           Installation URL (in Marketplace listing) to go through the
           Python-Social-Auth pipeline which we already have installed in the
           main application!

        4) Provision resources for customer - actually handled by the code below
    """
    http_method_names = ['get', 'head', 'options']

    def get(self, request, *args, **kwargs):
        """
            Read marketplace_purchase data for the currently logged in
            user and figure out how to provision resources.
        """
        # we take the most recent purchase event for this user
        purchase = Purchase.objects.filter(
            sender=request.user.username
        ).order_by('-received_on').first()

        if purchase.action == 'purchased':
            plan_price = purchase.marketplace_purchase['plan']['monthly_price_in_cents']

            # Free Marketplace plans have nothing to install so they
            # just redirect to the Public tenant
            if plan_price == 0:
                return HttpResponseRedirect('/')

            raise NotImplementedError('Paid plans are not supported yet')

        raise NotImplementedError(
            'Unsupported GitHub Marketplace action: "%s"' %
            purchase.action)
