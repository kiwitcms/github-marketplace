# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import hmac
import hashlib
from base64 import b64encode
from datetime import timedelta

from github import MainClass
from github.Requester import Requester

from social_django.models import UserSocialAuth

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseForbidden

from tcms.utils.user import delete_user


def verify_hmac(request):
    """
        Verifies request comes from FastSpring, see:
        https://docs.fastspring.com/integrating-with-fastspring/webhooks#Webhooks-securityMessageSecret/Security
    """
    received_signature = request.headers.get('X-FS-Signature', None)
    if not received_signature:
        return HttpResponseForbidden()

    # HMAC SHA256
    payload_signature = hmac.new(
        settings.KIWI_FASTSPRING_SECRET,
        msg=request.body,
        digestmod=hashlib.sha256).digest()
    # turn binary string into str !!!
    payload_signature = b64encode(payload_signature).decode()

    # due to security reasons do not use '==' operator
    # https://docs.python.org/3/library/hmac.html#hmac.compare_digest
    if not hmac.compare_digest(received_signature, payload_signature):
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
                       True, None)

    revoke_url = '/applications/%s/tokens/%s' % (settings.SOCIAL_AUTH_GITHUB_KEY, token)
    _headers, _data = gh_api.requestJsonAndCheck('DELETE', revoke_url)


def cancel_plan(purchase):
    """
        Cancells the current plan from Marketplace:
        https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/cancelling-plans/
    """
    customer = get_user_model().objects.filter(email=purchase.sender).first()

    # this can happen for users who have installed the FREE subscription
    # but their accounts were removed due to inactivity. Nothing else to do.
    if not customer:
        return HttpResponse('Sender not found', content_type='text/plain')

    if customer.is_superuser:
        return HttpResponse('super-user not deleted from DB', content_type='text/plain')

    # Deactivate the account of the customer who cancelled their plan.
    customer.is_active = False
    customer.save()

    # store token in a variable so we can remove it later
    customer_token = None
    user_social_auth = UserSocialAuth.objects.filter(user=customer).first()
    if user_social_auth:
        customer_token = user_social_auth.extra_data['access_token']

    # Remove tenant and all customer data across all tenants
    # before attempting to revoke GitHub token
    delete_user(customer)

    # Revoke the OAuth token your app received for the customer.
    if customer_token:
        try:
            revoke_oauth_token(customer_token)
        except:  # noqa:E722, pylint: disable=bare-except
            pass

    return HttpResponse('cancelled', content_type='text/plain')


def calculate_paid_until(mp_purchase, effective_date):
    """
        Calculates when access to paid services must be disabled.
    """
    paid_until = effective_date
    if mp_purchase['billing_cycle'] == 'monthly':
        paid_until += timedelta(days=31)
    elif mp_purchase['billing_cycle'] == 'yearly':
        paid_until += timedelta(days=366)

    # above we give them 1 extra day and here we always end at 23:59:59
    return paid_until.replace(hour=23, minute=59, second=59)


def organization_from_purchase(purchase):
    """
        Helps support organizational purchases
    """
    if purchase is None:
        return None

    if purchase.payload['marketplace_purchase']['account']['type'] == 'Organization':
        return purchase.payload['marketplace_purchase']['account']['login']

    return None
