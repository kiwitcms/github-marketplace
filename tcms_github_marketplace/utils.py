# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from datetime import datetime

from django.http import HttpResponseRedirect


def handle_purchased(payload):
    """
        Handle 'purchased' event, see:
        https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/github-marketplace-webhook-events/
    """
    plan_price = purchase['plan']['monthly_price_in_cents']

    # Free Marketplace plans have nothing to install so they
    # just redirect to the Public tenant, b/c the user is
    # already authenticated via OAuth!
    #
    # For now we don't even record this event in the database
    if plan_price == 0:
        return HttpResponseRedirect('/')


    # format is 2017-10-25T00:00:00+00:00
    effective_date = datetime.strptime(payload['effective_date'][:19],
                                       '%Y-%m-%dT%H:%M:%S')
    sender = payload['sender']['login']
    purchase = payload['marketplace_purchase']

    raise NotImplementedError('Paid plans are not supported yet')


def handle_cancelled(payload):
    raise NotImplementedError('Cancelling events is not implemeted yet')
