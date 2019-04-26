# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import hmac
import hashlib

from django.conf import settings
from django.http import HttpResponseForbidden


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
