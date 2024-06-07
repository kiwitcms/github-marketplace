# Copyright (c) 2022 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=missing-permission-required

from django.conf import settings
from mailchimp3 import MailChimp


def subscribe(email_address):
    try:
        client = MailChimp(
            mc_api=settings.MAILCHIMP_SECRET, mc_user=settings.MAILCHIMP_USERNAME
        )

        # add user to list "Kiwi TCMS newsletter"
        # status is 'pending', users must opt-in themselves!
        client.lists.members.create(
            "c970a37581",
            {
                "email_address": email_address,
                "status": "pending",
            },
        )
    except:  # noqa:E722, pylint: disable=bare-except
        # this avoids 500 errors due to invalid email address
        # or any other exception really
        pass
