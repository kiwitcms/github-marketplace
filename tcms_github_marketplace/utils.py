# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import hmac
import hashlib
from datetime import datetime, timedelta

from github import MainClass
from github.Requester import Requester

from social_django.models import UserSocialAuth

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseForbidden

from tcms.utils.user import delete_user


def calculate_signature(secret, contents):
    """
        Calculate GitHub signature header.

        WARNING: both parameters must be bytes, not string!
    """
    return 'sha1=' + hmac.new(
        secret,
        msg=contents,
        digestmod=hashlib.sha1).hexdigest()


def verify_signature(request):
    """
        Verifies request comes from GitHub, see:
        https://developer.github.com/webhooks/securing/
    """
    signature = request.headers.get('X-Hub-Signature', None)
    if not signature:
        return HttpResponseForbidden()

    expected = calculate_signature(settings.KIWI_GITHUB_MARKETPLACE_SECRET,
                                   request.body)

    # due to security reasons do not use '==' operator
    # https://docs.python.org/3/library/hmac.html#hmac.compare_digest
    if not hmac.compare_digest(signature, expected):
        return HttpResponseForbidden()

    return True  # b/c of inconsistent-return-statements


def revoke_oauth_token(token):
    """
        Revokes OAuth token:
        https://developer.github.com/v3/oauth_authorizations/#revoke-an-authorization-for-an-application
    """
    # note: Requester is the internal transport used by PyGithub
    # b/c it is missing this functionality built-in
    #
    # note2: GitHub documentation says that for this method we must
    # use Basic Authentication, where the username is the OAuth application
    # client_id and the password is its client_secret.
    gh_api = Requester(settings.SOCIAL_AUTH_GITHUB_KEY,
                       settings.SOCIAL_AUTH_GITHUB_SECRET,
                       None, MainClass.DEFAULT_BASE_URL,
                       MainClass.DEFAULT_TIMEOUT, None, None,
                       'KiwiTCMS/Python', MainClass.DEFAULT_PER_PAGE,
                       False, True, None)

    revoke_url = '/applications/%s/tokens/%s' % (settings.SOCIAL_AUTH_GITHUB_KEY, token)
    _headers, _data = gh_api.requestJsonAndCheck('DELETE', revoke_url)


def cancel_plan(purchase):
    """
        Cancells the current plan from Marketplace:
        https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/cancelling-plans/
    """
    customer = get_user_model().objects.get(username=purchase.sender)

    # Deactivate the account of the customer who cancelled their plan.
    customer.is_active = False
    customer.save()

    # store token in a variable so we can remove it later
    customer_token = UserSocialAuth.objects.get(user=customer).extra_data['access_token']

    # Remove tenand and all customer data across all tenants
    # before attempting to revoke GitHub token
    delete_user(customer)

    # Revoke the OAuth token your app received for the customer.
    revoke_oauth_token(customer_token)

    return HttpResponse('cancelled', content_type='text/plain')


def calculate_paid_until(mp_purchase, effective_date):
    """
        Calculates when access to paid services must be disabled.

        Note: until now we've seen GitHub send only payload where
        next_billing_date is None and this is what we test with.

        Most likely we need to update the calculation to take into
        account effective_date instead and not rely on next_billing_date
        at all !!!
    """
    paid_until = effective_date
    if mp_purchase['next_billing_date'] is None:
        if mp_purchase['billing_cycle'] == 'monthly':
            paid_until += timedelta(days=31)
        elif mp_purchase['billing_cycle'] == 'yearly':
            paid_until += timedelta(days=366)
    else:
        # format is 2017-10-25T00:00:00+00:00
        paid_until = datetime.strptime(mp_purchase['next_billing_date'][:19],
                                       '%Y-%m-%dT%H:%M:%S')

    # above we give them 1 extra day and here we always end at 23:59:59
    return paid_until.replace(hour=23, minute=59, second=59)
