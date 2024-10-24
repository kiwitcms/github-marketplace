# Copyright (c) 2019-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=too-many-ancestors
import json
from http import HTTPStatus
from unittest.mock import call
from unittest.mock import patch
from datetime import datetime

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model

from social_django.models import UserSocialAuth

from tcms.utils import github

import tcms_tenants

from tcms_github_marketplace import docker
from tcms_github_marketplace import mailchimp
from tcms_github_marketplace import utils
from tcms_github_marketplace.models import Purchase


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

    def test_recurring_billing_hook(self):
        """
        According to GitHub recurring billing events do not redirect to
        Install URL but only send webhook payloads so we must
        extend tenant.paid_until while handling the hook event
        """
        # tenant has expired
        # b/c we will update only tenants which
        # are currently/have been previously paid for !!!
        self.tenant.paid_until = datetime(2019, 3, 30, 23, 59, 59, 0)
        # just b/c the payload uses an organization
        self.tenant.organization = "kiwitcms"
        self.tenant.save()

        payload = """
{
   "action":"purchased",
   "effective_date":"2019-04-01T00:00:00+00:00",
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
         "login":"kiwitcms",
         "organization_billing_email":"username@email.com"
      },
      "billing_cycle":"monthly",
      "unit_count":1,
      "on_free_trial":false,
      "free_trial_ends_on":null,
      "next_billing_date":null,
      "plan":{
         "id":435,
         "name":"Public Tenant",
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
            self.tenant.owner.username,
            self.tenant.owner.email,
        )
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(json.loads(payload)).encode(),
        )

        # send marketplace_purchase hook
        response = self.client.post(
            self.url,
            json.loads(payload),
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE=signature,
        )
        self.assertContains(response, "ok")

        # paid_until date was increased minimum 30 days
        self.tenant.refresh_from_db()
        self.assertGreater(self.tenant.paid_until, datetime(2019, 5, 1, 23, 59, 59, 0))


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
            utils.Requester, "requestJsonAndCheck", return_value=({}, None)
        ) as gh_api, patch.object(
            docker.QuayIOAccount, "delete", return_value=""
        ) as quay_io_api:
            response = self.client.post(
                self.purchase_hook_url,
                json.loads(payload),
                content_type="application/json",
                HTTP_X_HUB_SIGNATURE=signature,
            )
            self.assertContains(response, "cancelled")
            gh_api.assert_called_with("DELETE", self.gh_revoke_url)
            quay_io_api.assert_called_once()

        # verify user is not present anymore
        self.assertFalse(
            get_user_model().objects.filter(username=self.tester.username).exists()
        )
