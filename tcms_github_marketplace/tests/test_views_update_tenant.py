# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=too-many-ancestors

from django.contrib.auth.models import Permission
from django.urls import reverse

import tcms_tenants.tests


class UpdateTenantTestCase(tcms_tenants.tests.LoggedInTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.edit_tenant_url = reverse("tcms_tenants:edit-tenant")
        cls.create_tenant_url = reverse("github_marketplace_create_tenant")
        cls.purchase_hook_url = reverse("github_marketplace_purchase_hook")

        cls.change_tenant = Permission.objects.get(
            content_type__app_label="tcms_tenants", codename="change_tenant"
        )
        cls.tester.user_permissions.add(cls.change_tenant)

        # update owner so the currently logged user during test execution
        # can edit the tenant
        cls.tenant.owner = cls.tester
        cls.tenant.save()

    @classmethod
    def use_existing_tenant(cls):
        cls.setup_tenant(cls.tenant)

    def test_editing_tenant_extra_emails_field_should_work(self):
        self.assertIsNone(self.tenant.extra_emails)

        # GET the Edit tenant page should display the extra_emails field
        response = self.client.get(self.edit_tenant_url)
        self.assertContains(
            response,
            '<input type="text" id="id_extra_emails" maxlength="256" '
            'placeholder="technical@example.bg; billing@example.bg" '
            'name="extra_emails" value="" class="form-control">',
            html=True,
        )

        # send a POST request to update the values
        response = self.client.post(
            self.edit_tenant_url,
            {
                "name": "After Edits",
                "owner": self.tester.pk,
                "extra_emails": "billing@example.org; admin@example.net",
            },
        )
        # should still redirect to the tenant which was created in the previous step
        self.assertRedirects(response, "/")

        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.name, "After Edits")
        self.assertEqual(
            self.tenant.extra_emails, "billing@example.org; admin@example.net"
        )
