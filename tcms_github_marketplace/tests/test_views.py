# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import json
from http import HTTPStatus
from unittest.mock import patch

from django.urls import reverse
from django.conf import settings
from django.test import TestCase
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model

from social_django.models import UserSocialAuth

from tcms_github_marketplace import utils
from tcms_github_marketplace.tests import LoggedInTestCase


class PurchaseHookTestCase(TestCase):
    def setUp(self):
        self.url = reverse('github_marketplace_purchase_hook')

    def test_without_signature_header(self):
        payload = json.loads("""
{
   "action":"purchased",
   "effective_date":"2017-10-25T00:00:00+00:00",
   "sender":{
      "login":"username",
      "id":3877742,
      "avatar_url":"https://avatars2.githubusercontent.com/u/3877742?v=4",
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
         "id":18404719,
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
""".strip())
        response = self.client.post(self.url, payload, content_type='application/json')

        # missing signature should cause failure
        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_purchased_free_plan(self):
        payload = """
{
   "action":"purchased",
   "effective_date":"2017-10-25T00:00:00+00:00",
   "sender":{
      "login":"username",
      "id":3877742,
      "avatar_url":"https://avatars2.githubusercontent.com/u/3877742?v=4",
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
         "id":18404719,
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
        signature = utils.calculate_signature(settings.KIWI_GITHUB_MARKETPLACE_SECRET,
                                              json.dumps(json.loads(payload)).encode())

        # the hook handler does nothing but save to DB
        with self.assertNumQueries(1):
            response = self.client.post(self.url,
                                        json.loads(payload),
                                        content_type='application/json',
                                        HTTP_X_HUB_SIGNATURE=signature)
            self.assertContains(response, 'ok')

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
        signature = utils.calculate_signature(settings.KIWI_GITHUB_MARKETPLACE_SECRET,
                                              json.dumps(json.loads(payload)).encode())
        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='ping')

        # initial ping responds with a pong
        self.assertContains(response, 'pong')


class InstallTestCase(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.purchase_hook_url = reverse('github_marketplace_purchase_hook')
        cls.install_url = reverse('github_marketplace_install')

    def test_purchased_free_plan(self):
        payload = """
{
   "action":"purchased",
   "effective_date":"2017-10-25T00:00:00+00:00",
   "sender":{
      "login":"%s",
      "id":3877742,
      "avatar_url":"https://avatars2.githubusercontent.com/u/3877742?v=4",
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
         "id":18404719,
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
""".strip() % (self.tester.username, self.tester.username)
        signature = utils.calculate_signature(settings.KIWI_GITHUB_MARKETPLACE_SECRET,
                                              json.dumps(json.loads(payload)).encode())

        # first simulate marketplace_purchase hook
        response = self.client.post(self.purchase_hook_url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature)
        self.assertContains(response, 'ok')

        # then simulate redirection to Installation URL
        response = self.client.get(self.install_url)

        # purchases for free plan redirect to / on public tenant
        self.assertRedirects(response, '/')



class CancelPlanTestCase(InstallTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # simulate existing GitHub login
        UserSocialAuth.objects.create(
            user=cls.tester,
            provider='github',
            uid='12345',
            extra_data={"access_token": "TEST-ME", "token_type": "bearer"})
        cls.gh_revoke_url = '/applications/%s/tokens/TEST-ME' % settings.SOCIAL_AUTH_GITHUB_KEY

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
    "email": "bot@kiwitcms.org"
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
""".strip() % (self.tester.username, self.tester.username)
        signature = utils.calculate_signature(settings.KIWI_GITHUB_MARKETPLACE_SECRET,
                                              json.dumps(json.loads(payload)).encode())

        with patch.object(utils.Requester,
                          'requestJsonAndCheck',
                          return_value=({}, None)) as gh_api:
            response = self.client.post(self.purchase_hook_url,
                                        json.loads(payload),
                                        content_type='application/json',
                                        HTTP_X_HUB_SIGNATURE=signature)
            self.assertContains(response, 'cancelled')
            gh_api.assert_called_with('DELETE', self.gh_revoke_url)

        # verify user is not present anymore
        self.assertFalse(get_user_model().objects.filter(username=self.tester.username).exists())