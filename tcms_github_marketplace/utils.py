# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
import hmac
import hashlib
from datetime import datetime

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect


def verify_signature(request):
    """
        Verifies request comes from GitHub, see:
        https://developer.github.com/webhooks/securing/
    """
    signature = request.META.get('HTTP_X_HUB_SIGNATURE', None)
    if not signature:
        return HttpResponseForbidden()

    expected = 'sha1=' + hmac.new(  # pylint: disable=no-member
        settings.KIWI_GITHUB_MARKETPLACE_SECRET,
        msg=request.POST,
        digestmod=hashlib.sha1).hex()

    if not hmac.compare_digest(signature, expected):
        return HttpResponseForbidden()

    return True  # b/c of inconsistent-return-statements


def handle_purchased(payload):
    """
        Handle 'purchased' event, see:
        https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/github-marketplace-webhook-events/
    """
    # format is 2017-10-25T00:00:00+00:00
    effective_date = datetime.strptime(payload['effective_date'][:19],
                                       '%Y-%m-%dT%H:%M:%S')
    sender = payload['sender']['login']
    purchase = payload['marketplace_purchase']
    plan_price = purchase['plan']['monthly_price_in_cents']

    # Free Marketplace plans have nothing to install so they
    # just redirect to the Public tenant, b/c the user is
    # already authenticated via OAuth!
    #
    # For now we don't even record this event in the database
    if plan_price == 0:
        return HttpResponseRedirect('/')

    raise NotImplementedError('Paid plans are not supported yet')


def handle_cancelled(payload):
    raise NotImplementedError('Cancelling events is not implemeted yet')