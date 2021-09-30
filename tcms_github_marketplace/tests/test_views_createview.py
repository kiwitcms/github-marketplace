# Copyright (c) 2019-2021 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors
import json
from datetime import datetime, timedelta

from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.test import RequestFactory

from tcms.utils import github

import tcms_tenants


class CreateTenantTestCase(tcms_tenants.tests.LoggedInTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.create_tenant_url = reverse('github_marketplace_create_tenant')
        cls.purchase_hook_url = reverse('github_marketplace_purchase_hook')

        # Make sure we don't have any permissions set up b/c
        # tcms_tenants.views.NewTenantsView requires permissions while
        # CreateTenant is supposed to jump over that
        cls.tester.user_permissions.all().delete()

    @classmethod
    def use_existing_tenant(cls):
        cls.setup_tenant(cls.tenant)

    @classmethod
    def setup_tenant(cls, tenant):
        super().setup_tenant(tenant)
        tenant.organization = ""  # instead of None
        tenant.save()

    def tearDown(self):
        self.client.logout()
        super().tearDown()

    def test_invalid_schema_name_shows_errors(self):
        payload = """
{
   "action":"purchased",
   "effective_date":"2019-04-01T00:00:00+00:00",
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
      "email":"%s"
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
""".strip() % (self.tester.username, self.tester.email, self.tester.username)
        payload = json.loads(payload)
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(payload).encode())

        # first simulate marketplace_purchase hook
        response = self.client.post(self.purchase_hook_url,
                                    payload,
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature)
        self.assertContains(response, 'ok')

        # try creating a new tenant with invalid schema_name
        expected_paid_until = datetime(2019, 5, 2, 23, 59, 59, 0)
        expected_paid_until = expected_paid_until.isoformat().replace('T', ' ')

        response = self.client.post(
            self.create_tenant_url,
            {
                'name': 'Dash Is Not Allowed',
                'schema_name': 'kiwi-tcms',
                'publicly_readable': False,
                'paid_until': expected_paid_until,
            })

        self.assertContains(response, 'Invalid string')
        self.assertContains(response, 'Validation pattern: ^[a-z0-9]{1,63}$')
        self.assertFalse(
            tcms_tenants.models.Tenant.objects.filter(schema_name='kiwi-tcms').exists())

    def test_visit_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.create_tenant_url)

        # requires login
        self.assertRedirects(
            response,
            reverse('tcms-login') + f'?next={self.create_tenant_url}')

    def test_visit_without_purchase(self):
        """
            If user visits the Create Tenant page
            without having purchased plans from Marketplace first.
        """
        response = self.client.get(self.create_tenant_url)

        # redirect to / on public tenant
        self.assertRedirects(response, '/')

    def test_visit_after_creation(self):
        """
            If user visits the Create Tenant page
            when they already have a tenant created
        """
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
      "email":"%s"
   },
   "marketplace_purchase":{
      "account":{
         "type":"User",
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
""".strip() % (self.tenant.owner.username,
               self.tenant.owner.email,
               self.tenant.owner.username)
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(json.loads(payload)).encode())

        # first simulate marketplace_purchase hook
        response = self.client.post(self.purchase_hook_url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature)
        self.assertContains(response, 'ok')

        # now login as the tenant owner
        self.client.login(username=self.tenant.owner.username,  # nosec:B106
                          password='password')

        # and visit again the create tenant page
        response = self.client.get(self.create_tenant_url)

        fake_request = RequestFactory().get(self.create_tenant_url)
        fake_request.user = self.tenant.owner
        expected_url = tcms_tenants.utils.tenant_url(
            fake_request, self.tenant.schema_name)

        # redirects to / on own tenant
        self.assertRedirects(response, expected_url,
                             fetch_redirect_response=False)

    def test_visit_superuser(self):
        """
            Superuser can always create new tenant
        """
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
      "email":"%s"
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
""".strip() % (self.tenant.owner.username,
               self.tenant.owner.email,
               self.tenant.owner.username)
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(json.loads(payload)).encode())

        # first simulate marketplace_purchase hook
        response = self.client.post(self.purchase_hook_url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature)
        self.assertContains(response, 'ok')

        # make tenant owner superuser
        self.tenant.owner.is_superuser = True
        self.tenant.owner.save()

        # now login as the tenant owner
        self.client.login(username=self.tenant.owner.username,  # nosec:B106
                          password='password')

        # and visit again the create tenant page
        response = self.client.get(self.create_tenant_url)

        # shows Create Tenant page
        self.assertContains(response, 'New tenant')

    def test_visit_after_purchase(self):
        """
            If user visits the Create Tenant page
            after they've purchased a subscription plan
            then they should be able to see the create tenant form
            with extra fields populated.
        """
        payload = """
{
   "action":"purchased",
   "effective_date":"2019-04-01T00:00:00+00:00",
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
      "email":"%s"
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
""".strip() % (self.tester.username, self.tester.email, self.tester.username)
        payload = json.loads(payload)
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(payload).encode())

        # first simulate marketplace_purchase hook
        response = self.client.post(self.purchase_hook_url,
                                    payload,
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature)
        self.assertContains(response, 'ok')

        # visit the create tenant page
        response = self.client.get(self.create_tenant_url)
        expected_paid_until = datetime(2019, 5, 2, 23, 59, 59, 0)
        expected_paid_until = expected_paid_until.isoformat().replace('T', ' ')

        self.assertContains(response, 'New tenant')
        self.assertContains(response, 'Private Tenant Warning')
        self.assertContains(response, f'action="{self.create_tenant_url}"')
        self.assertContains(response, 'Paid until')
        self.assertContains(response, 'Validation pattern: ^[a-z0-9]{1,63}$')
        self.assertContains(
            response,
            '<input type="hidden" name="paid_until"'
            f' value="{expected_paid_until}" id="id_paid_until">',
            html=True)
        self.assertContains(
            response,
            'class="bootstrap-switch" name="publicly_readable" type="checkbox"')
        self.assertContains(response, 'Owner')
        self.assertContains(response, f"<label>{self.tester.username}</label>")

        self.assertContains(response, 'Organization')
        self.assertContains(response, f"<label>{self.tester.username}</label>")

    def test_visit_after_free_purchase(self):
        """
            If user visits the Create Tenant page
            after they've purchased a FREE plan
            then must be redirected to / .
        """
        payload = """
{
   "action":"purchased",
   "effective_date":"2019-04-01T00:00:00+00:00",
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
      "email":"%s"
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
      "next_billing_date":null,
      "plan":{
         "id":435,
         "name":"Public Tenant",
         "description":"Basic Plan",
         "monthly_price_in_cents":0,
         "yearly_price_in_cents":0,
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
""".strip() % (self.tester.username, self.tester.email, self.tester.username)
        payload = json.loads(payload)
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(payload).encode())

        # first simulate marketplace_purchase hook
        response = self.client.post(self.purchase_hook_url,
                                    payload,
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature)
        self.assertContains(response, 'ok')

        # visit the create tenant page
        response = self.client.get(self.create_tenant_url)

        # redirects to / on public tenant
        self.assertRedirects(response, '/')

    def test_creating_tenant_after_purchase_should_work(self):
        payload = """
{
   "action":"purchased",
   "effective_date":"2021-08-20T00:00:00+00:00",
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
      "email":"%s"
   },
   "marketplace_purchase":{
      "account":{
         "type":"User",
         "id":18404719,
         "login":"%s",
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
""".strip() % (self.tester.username, self.tester.email, self.tester.username)
        payload = json.loads(payload)
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_MARKETPLACE_SECRET,
            json.dumps(payload).encode())

        # first simulate marketplace_purchase hook
        response = self.client.post(self.purchase_hook_url,
                                    payload,
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature)
        self.assertContains(response, 'ok')

        # create the tenant
        response = self.client.post(
            self.create_tenant_url,
            {
                'name': 'Tenant, Inc.',
                'schema_name': 'tinc',
                # this is what the default form view sends
                'owner': self.tester.pk,
                'organization': '',
                'publicly_readable': False,
                'paid_until': timezone.now() + timedelta(days=30),
            }
        )

        fake_request = RequestFactory().get(self.create_tenant_url)
        fake_request.user = self.tester
        expected_url = tcms_tenants.utils.tenant_url(fake_request, "tinc")
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

        tenant = tcms_tenants.models.Tenant.objects.get(schema_name='tinc')
        self.assertEqual(tenant.owner, self.tester)

        # Simulate POST refresh after a 504 with a possible change in values
        response = self.client.post(
            self.create_tenant_url,
            {
                'name': '2nd Tenant, Inc.',
                'schema_name': 'tinc2',
                # this is what the default form view sends
                'owner': self.tester.pk,
                'organization': '',
                'publicly_readable': False,
                'paid_until': timezone.now() + timedelta(days=30),
            }
        )
        # should still redirect to the tenant which was created in the previous step
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

    def test_post_to_create_tenant_without_purchase_should_not_work(self):
        response = self.client.post(
            self.create_tenant_url,
            {
                'name': 'Second Tenant',
                'schema_name': 't2',
                # this is what the default form view sends
                'owner': self.tester.pk,
                'publicly_readable': False,
                'paid_until': timezone.now() + timedelta(days=30),
            }
        )
        self.assertRedirects(response, '/')

        tenant = tcms_tenants.models.Tenant.objects.filter(schema_name='t2').first()
        self.assertIsNone(tenant)
