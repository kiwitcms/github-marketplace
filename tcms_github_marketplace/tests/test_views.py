# Copyright (c) 2019-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=too-many-ancestors
import json

from http import HTTPStatus
from unittest.mock import call
from unittest.mock import patch
from datetime import timedelta

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone

from social_django.models import UserSocialAuth

from tcms.utils import github

import tcms_tenants

from tcms_github_marketplace import docker
from tcms_github_marketplace import mailchimp
from tcms_github_marketplace.models import Purchase
from tcms_github_marketplace.cron_github_recurring_billing import (
    check_github_for_subscription_renewals,
)


class PurchaseHookTestCase(tcms_tenants.tests.LoggedInTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("github_marketplace_purchase_hook")

    def test_without_signature_header(self):
        payload = json.loads(
            """
{
   "action":"purchased",
   "effective_date":"2017-10-25T00:00:00+00:00",
   "sender":{
      "login":"username",
      "id":9990009999,
      "avatar_url":"https://avatars2.githubusercontent.com/u/9990009999?v=4",
      "gravatar_id":"",
      "url":"https://api.github.com/users/username",
      "html_url":"https://github.com/username",
      "followers_url":"https://api.github.com/users/username/followers",
      "following_url":"https://api.github.com/users/username/following{/other_user}",
      "gists_url":"https://api.github.com/users/username/gists{/gist_id}",
      "starred_url":"https://api.github.com/users/username/starred{/owner}{/repo}",
      "subscriptions_url":"https://api.github.com/users/username/subscriptions",
      "organizations_url":"https://api.github.com/users/username/orgs",
      "repos_url":"https://api.github.com/users/username/repos",
      "events_url":"https://api.github.com/users/username/events{/privacy}",
      "received_events_url":"https://api.github.com/users/username/received_events",
      "type":"User",
      "site_admin":true,
      "email":"username@email.com"
   },
   "marketplace_purchase":{
      "account":{
         "type":"Organization",
         "id":999999999,
         "login":"username",
         "organization_billing_email":"username@email.com"
      },
      "billing_cycle":"monthly",
      "unit_count":1,
      "on_free_trial":false,
      "free_trial_ends_on":null,
      "next_billing_date":"2017-11-05T00:00:00+00:00",
      "plan":{
         "id":435,
         "name":"Public Tenant",
         "description":"Basic Plan",
         "monthly_price_in_cents":0,
         "yearly_price_in_cents":0,
         "price_model":"free",
         "has_free_trial":true,
         "unit_name":"seat",
         "bullets":[
            "Is Basic",
            "Because Basic "
         ]
      }
   }
}
""".strip()
        )
        response = self.client.post(self.url, payload, content_type="application/json")

        # missing signature should cause failure
        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_with_valid_signature_header(self):
        payload = """
{
   "action":"purchased",
   "effective_date":"2017-10-25T00:00:00+00:00",
   "sender":{
      "login":"username",
      "id":9990009999,
      "avatar_url":"https://avatars2.githubusercontent.com/u/9990009999?v=4",
      "gravatar_id":"",
      "url":"https://api.github.com/users/username",
      "html_url":"https://github.com/username",
      "followers_url":"https://api.github.com/users/username/followers",
      "following_url":"https://api.github.com/users/username/following{/other_user}",
      "gists_url":"https://api.github.com/users/username/gists{/gist_id}",
      "starred_url":"https://api.github.com/users/username/starred{/owner}{/repo}",
      "subscriptions_url":"https://api.github.com/users/username/subscriptions",
      "organizations_url":"https://api.github.com/users/username/orgs",
      "repos_url":"https://api.github.com/users/username/repos",
      "events_url":"https://api.github.com/users/username/events{/privacy}",
      "received_events_url":"https://api.github.com/users/username/received_events",
      "type":"User",
      "site_admin":true,
      "email":"username@email.com"
   },
   "marketplace_purchase":{
      "account":{
         "type":"Organization",
         "id":999999999,
         "login":"example-org",
         "organization_billing_email":"username@email.com"
      },
      "billing_cycle":"monthly",
      "unit_count":1,
      "on_free_trial":false,
      "free_trial_ends_on":null,
      "next_billing_date":"2017-11-05T00:00:00+00:00",
      "plan":{
         "id":435,
         "name":"Public Tenant",
         "description":"Basic Plan",
         "monthly_price_in_cents":5000,
         "yearly_price_in_cents":60000,
         "price_model":"free",
         "has_free_trial":true,
         "unit_name":"seat",
         "bullets":[
            "Is Basic",
            "Because Basic ",
            "Docker repositories: quay.io/kiwitcms/version, https://quay.io/kiwitcms/enterprise"
         ]
      }
   }
}
""".strip()
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(json.loads(payload)).encode(),
        )

        initial_purchase_count = Purchase.objects.count()

        # tmp_account calculates the actual robot name for mocking - currently not in use
        with docker.QuayIOAccount("username@email.com") as tmp_account:
            with patch.object(
                docker.QuayIOAccount,
                "create",
                return_value={"name": tmp_account.name, "token": "secret"},
            ) as quay_io_create, patch.object(
                docker.QuayIOAccount,
                "allow_read_access",
                return_value="success",
            ) as quay_io_allow_read_access, patch.object(
                mailchimp,
                "subscribe",
                return_value="success",
            ) as mailchimp_subscribe:
                response = self.client.post(
                    self.url,
                    json.loads(payload),
                    content_type="application/json",
                    HTTP_X_HUB_SIGNATURE=signature,
                )
                self.assertContains(response, "ok")
                quay_io_create.assert_called_once()
                quay_io_allow_read_access.assert_has_calls(
                    [call("version"), call("enterprise")], any_order=True
                )
                mailchimp_subscribe.assert_called_once_with("username@email.com")

        # the hook handler does nothing but save to DB
        self.assertEqual(initial_purchase_count + 1, Purchase.objects.count())

        # make sure the prefix was recorded
        purchase = Purchase.objects.order_by("pk").last()
        self.assertEqual(purchase.gitops_prefix, "https://github.com/example-org")

    def test_hook_ping(self):
        payload = """
{
  "zen": "Mind your words, they are important.",
  "hook_id": 1234,
  "hook": {
    "type": "Marketplace::Listing",
    "id": 1234,
    "name": "web",
    "active": true,
    "events": [
      "*"
    ],
    "config": {
      "content_type": "json",
      "url": "https://kiwitcms.org/hook/",
      "insecure_ssl": "0"
    },
    "updated_at": "2019-04-23T13:23:59Z",
    "created_at": "2019-04-23T13:23:59Z",
    "marketplace_listing_id": 1234
  },
  "sender": {
    "login": "atodorov",
    "id": 1002300
  }
}
""".strip()
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(json.loads(payload)).encode(),
        )
        response = self.client.post(
            self.url,
            json.loads(payload),
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE=signature,
            HTTP_X_GITHUB_EVENT="ping",
        )

        # initial ping responds with a pong
        self.assertContains(response, "pong")

    @override_settings(
        KIWI_GITHUB_APP_ID=1234,
        KIWI_GITHUB_APP_PRIVATE_KEY="this-is-the-key",
    )
    def test_recurring_billing_check(self):
        now = timezone.now()

        # Purchase made 35 days ago
        _35_days_ago = now - timedelta(days=35)
        # this is when a recurring purchase was supposed to happen
        # but for some reason it didn't go through
        _4_days_ago = now - timedelta(days=4)

        old_purchase = Purchase.objects.create(
            vendor="github",
            action="purchased",
            sender=self.tenant.owner.email,
            received_on=_35_days_ago,
            effective_date=_35_days_ago,
            payload={
                "action": "purchased",
                "effective_date": _35_days_ago.strftime("%Y-%m-%dT%H:%M:%S"),
                "sender": {
                    "login": self.tenant.owner.username,
                    "id": 9990009999,
                    "type": "User",
                    "email": self.tenant.owner.email,
                },
                "marketplace_purchase": {
                    "account": {
                        "type": "Organization",
                        "id": 999999999,
                        "login": "kiwitcms",
                        "organization_billing_email": "username@email.com",
                    },
                    "billing_cycle": "monthly",
                    "next_billing_date": _4_days_ago.strftime("%Y-%m-%dT%H:%M:%S"),
                    "plan": {
                        "bullets": [
                            "1x SaaS hosting under *.tenant.kiwitcms.org",
                            "Docker repositories: quay.io/kiwitcms/version",
                            "Always the latest version",
                            "09-17 UTC/Mon-Fri support ",
                        ],
                        "description": "Unlimited users. Control "
                        "who can access. Ideal for "
                        "small teams.",
                        "has_free_trial": False,
                        "id": 7335,
                        "monthly_price_in_cents": 5000,
                        "name": "Private Tenant",
                        "yearly_price_in_cents": 60000,
                    },
                },
            },
        )
        old_purchase.received_on = _35_days_ago
        old_purchase.save()

        # Tenant expired 4 days ago (Purchase.received_on + 31)
        # lets say customer forgot to update card details!
        self.tenant.paid_until = _4_days_ago
        self.tenant.organization = "kiwitcms"
        self.tenant.save()

        with patch("github.Requester.Requester.requestJsonAndCheck") as mocked_func:
            # simulate a payment which was just made after customer
            # has updated their card details
            mocked_func.return_value = (
                {},
                {
                    "id": 999999999,
                    "login": "kiwitcms",
                    "marketplace_pending_change": None,
                    "marketplace_purchase": {
                        "billing_cycle": "monthly",
                        "free_trial_ends_on": None,
                        "is_installed": True,
                        "next_billing_date": (now + timedelta(days=30)).strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        ),
                        "on_free_trial": False,
                        "plan": {
                            "bullets": [
                                "1x SaaS hosting under *.tenant.kiwitcms.org",
                                "Docker repositories: quay.io/kiwitcms/version",
                                "Always the latest version",
                                "09-17 UTC/Mon-Fri support ",
                            ],
                            "description": "Unlimited users. Control "
                            "who can access. Ideal for "
                            "small teams.",
                            "has_free_trial": False,
                            "id": 7335,
                            "monthly_price_in_cents": 5000,
                            "name": "Private Tenant",
                            "number": 5,
                            "price_model": "FLAT_RATE",
                            "state": "published",
                            "unit_name": None,
                            "url": "https://api.github.com/marketplace_listing/plans/7335",
                            "yearly_price_in_cents": 60000,
                        },
                        "unit_count": 1,
                    },
                    "organization_billing_email": "username@email.com",
                    "type": "Organization",
                    "url": "https://api.github.com/orgs/kiwitcms",
                },
            )

            # then cron job comes and checks whether subscription has been renewed
            check_github_for_subscription_renewals()

        # a new purchase was recorded in DB
        new_purchase = Purchase.objects.order_by("-received_on").first()
        self.assertEqual(new_purchase.vendor, "github_cron")
        self.assertEqual(new_purchase.sender, old_purchase.sender)
        self.assertEqual(
            new_purchase.payload["marketplace_purchase"]["account"]["id"],
            old_purchase.payload["marketplace_purchase"]["account"]["id"],
        )
        self.assertGreater(
            new_purchase.next_billing_date,
            old_purchase.next_billing_date + timedelta(days=30),
        )

        # paid_until date was increased minimum 30 days
        self.tenant.refresh_from_db()
        self.assertGreater(self.tenant.paid_until, now + timedelta(days=30))

    @override_settings(
        KIWI_GITHUB_APP_ID=1234,
        KIWI_GITHUB_APP_PRIVATE_KEY="this-is-the-key",
    )
    def test_recurring_billing_should_not_create_duplicate_record_if_already_renewed(
        self,
    ):
        # simulate cron job executing once
        self.test_recurring_billing_check()
        old_purchase_count = Purchase.objects.count()

        # then simulate it executing again on the next day
        check_github_for_subscription_renewals()

        new_purchase_count = Purchase.objects.count()

        # a new purchase was NOT recorded in DB
        self.assertEqual(new_purchase_count, old_purchase_count)


class InstallTestCase(tcms_tenants.tests.LoggedInTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_hook_url = reverse("github_marketplace_purchase_hook")
        cls.install_url = reverse("github_marketplace_install")

    def test_purchased_free_plan(self):
        payload = """
{
   "action":"purchased",
   "effective_date":"2017-10-25T00:00:00+00:00",
   "sender":{
      "login":"%s",
      "id":9990009999,
      "avatar_url":"https://avatars2.githubusercontent.com/u/9990009999?v=4",
      "gravatar_id":"",
      "url":"https://api.github.com/users/username",
      "html_url":"https://github.com/username",
      "followers_url":"https://api.github.com/users/username/followers",
      "following_url":"https://api.github.com/users/username/following{/other_user}",
      "gists_url":"https://api.github.com/users/username/gists{/gist_id}",
      "starred_url":"https://api.github.com/users/username/starred{/owner}{/repo}",
      "subscriptions_url":"https://api.github.com/users/username/subscriptions",
      "organizations_url":"https://api.github.com/users/username/orgs",
      "repos_url":"https://api.github.com/users/username/repos",
      "events_url":"https://api.github.com/users/username/events{/privacy}",
      "received_events_url":"https://api.github.com/users/username/received_events",
      "type":"User",
      "site_admin":true,
      "email":"%s"
   },
   "marketplace_purchase":{
      "account":{
         "type":"Organization",
         "id":999999999,
         "login":"%s",
         "organization_billing_email":"username@email.com"
      },
      "billing_cycle":"monthly",
      "unit_count":1,
      "on_free_trial":false,
      "free_trial_ends_on":null,
      "next_billing_date":"2017-11-05T00:00:00+00:00",
      "plan":{
         "id":435,
         "name":"Public Tenant",
         "description":"Basic Plan",
         "monthly_price_in_cents":0,
         "yearly_price_in_cents":0,
         "price_model":"free",
         "has_free_trial":true,
         "unit_name":"seat",
         "bullets":[
            "Is Basic",
            "Because Basic "
         ]
      }
   }
}
""".strip() % (
            self.tester.username,
            self.tester.email,
            self.tester.username,
        )
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(json.loads(payload)).encode(),
        )

        # first simulate marketplace_purchase hook
        response = self.client.post(
            self.purchase_hook_url,
            json.loads(payload),
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE=signature,
        )
        self.assertContains(response, "ok")

        # then simulate redirection to Installation URL
        response = self.client.get(self.install_url)

        # purchases for free plan redirect to / on public tenant
        self.assertRedirects(response, "/")


class OtherInstallTestCase(tcms_tenants.tests.LoggedInTestCase):
    """
    InstallTestCase is kind of special b/c it provides
    a method which simulates a FREE plan install and is also
    used in inherited classes.

    This class OTOH contains the rest of the test scenarios for
    the installation view.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.install_url = reverse("github_marketplace_install")
        cls.purchase_hook_url = reverse("github_marketplace_purchase_hook")

    def test_visit_without_purchase(self):
        """
        For when users manage to visit the installation URL
        without having purchased plans from Marketplace first.
        See KIWI-TCMS-7D:
        https://sentry.io/organizations/open-technologies-bulgaria-ltd/issues/1011970996/
        """
        # visit Installation URL
        response = self.client.get(self.install_url)

        # redirect to / on public tenant
        self.assertRedirects(response, "/")

    def test_purchased_private_tenant_plan(self):
        payload = """
{
   "action":"purchased",
   "effective_date":"2017-10-25T00:00:00+00:00",
   "sender":{
      "login":"%s",
      "id":9990009999,
      "avatar_url":"https://avatars2.githubusercontent.com/u/9990009999?v=4",
      "gravatar_id":"",
      "url":"https://api.github.com/users/username",
      "html_url":"https://github.com/username",
      "followers_url":"https://api.github.com/users/username/followers",
      "following_url":"https://api.github.com/users/username/following{/other_user}",
      "gists_url":"https://api.github.com/users/username/gists{/gist_id}",
      "starred_url":"https://api.github.com/users/username/starred{/owner}{/repo}",
      "subscriptions_url":"https://api.github.com/users/username/subscriptions",
      "organizations_url":"https://api.github.com/users/username/orgs",
      "repos_url":"https://api.github.com/users/username/repos",
      "events_url":"https://api.github.com/users/username/events{/privacy}",
      "received_events_url":"https://api.github.com/users/username/received_events",
      "type":"User",
      "site_admin":true,
      "email":"%s"
   },
   "marketplace_purchase":{
      "account":{
         "type":"Organization",
         "id":999999999,
         "login":"%s",
         "organization_billing_email":"username@email.com"
      },
      "billing_cycle":"monthly",
      "unit_count":1,
      "on_free_trial":false,
      "free_trial_ends_on":null,
      "next_billing_date":"2017-11-05T00:00:00+00:00",
      "plan":{
         "id":435,
         "name":"Private Tenant",
         "description":"Basic Plan",
         "monthly_price_in_cents":3200,
         "yearly_price_in_cents":32000,
         "price_model":"flat",
         "has_free_trial":true,
         "unit_name":"seat",
         "bullets":[
            "Is Basic",
            "Because Basic "
         ]
      }
   }
}
""".strip() % (
            self.tester.username,
            self.tester.email,
            self.tester.username,
        )
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(json.loads(payload)).encode(),
        )

        # first simulate marketplace_purchase hook
        response = self.client.post(
            self.purchase_hook_url,
            json.loads(payload),
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE=signature,
        )
        self.assertContains(response, "ok")

        # then simulate redirection to Installation URL
        response = self.client.get(self.install_url)

        # purchases for paid plans redirect to Create Tenant page
        self.assertRedirects(response, reverse("github_marketplace_create_tenant"))


class CancelPlanTestCase(InstallTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # simulate existing GitHub login
        UserSocialAuth.objects.create(
            user=cls.tester,
            provider="github",
            uid="12345",
            extra_data={"access_token": "TEST-ME", "token_type": "bearer"},
        )
        cls.gh_revoke_url = (
            f"/applications/{settings.SOCIAL_AUTH_GITHUB_APP_KEY}/tokens/TEST-ME"
        )

    def test_purchased_free_plan(self):
        # override so we don't execute it twice inside this class
        pass

    def test_cancelled_plan(self):
        # the user must have purchased a plan before
        super().test_purchased_free_plan()

        # now we try to cancel it
        payload = """
{
  "action": "cancelled",
  "effective_date": "2019-04-27T00:00:00+00:00",
  "sender": {
    "login": "%s",
    "id": 44892260,
    "node_id": "MDQ6VXNlcjQ0ODkyMjYw",
    "avatar_url": "https://avatars3.githubusercontent.com/u/44892260?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/kiwitcms-bot",
    "html_url": "https://github.com/kiwitcms-bot",
    "followers_url": "https://api.github.com/users/kiwitcms-bot/followers",
    "following_url": "https://api.github.com/users/kiwitcms-bot/following{/other_user}",
    "gists_url": "https://api.github.com/users/kiwitcms-bot/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/kiwitcms-bot/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/kiwitcms-bot/subscriptions",
    "organizations_url": "https://api.github.com/users/kiwitcms-bot/orgs",
    "repos_url": "https://api.github.com/users/kiwitcms-bot/repos",
    "events_url": "https://api.github.com/users/kiwitcms-bot/events{/privacy}",
    "received_events_url": "https://api.github.com/users/kiwitcms-bot/received_events",
    "type": "User",
    "site_admin": false,
    "email": "%s"
  },
  "marketplace_purchase": {
    "account": {
      "type": "User",
      "id": 44892260,
      "node_id": "MDQ6VXNlcjQ0ODkyMjYw",
      "login": "%s",
      "organization_billing_email": null
    },
    "billing_cycle": "monthly",
    "unit_count": 0,
    "on_free_trial": false,
    "free_trial_ends_on": null,
    "next_billing_date": null,
    "plan": {
      "id": 2254,
      "name": "Public Tenant",
      "description": "For product exploration and demo purposes.",
      "monthly_price_in_cents": 0,
      "yearly_price_in_cents": 0,
      "price_model": "free",
      "has_free_trial": false,
      "unit_name": null,
      "bullets": [
        "Other users have access to your data",
        "Inactive users removed after 90 days",
        "Hosted at public.tenant.kiwitcms.org",
        "SSL enabled"
      ]
    }
  }
}
""".strip() % (
            self.tester.username,
            self.tester.email,
            self.tester.username,
        )
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(json.loads(payload)).encode(),
        )

        with patch.object(
            docker.QuayIOAccount, "delete", return_value=""
        ) as quay_io_api:
            response = self.client.post(
                self.purchase_hook_url,
                json.loads(payload),
                content_type="application/json",
                HTTP_X_HUB_SIGNATURE=signature,
            )
            self.assertContains(response, "cancelled")
            quay_io_api.assert_called_once()

        # verify user is still present
        self.assertTrue(
            get_user_model().objects.filter(username=self.tester.username).exists()
        )
