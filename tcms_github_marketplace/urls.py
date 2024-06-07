# Copyright (c) 2019-2022 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.urls import re_path
from tcms_github_marketplace import views


urlpatterns = [
    re_path(
        r"^purchase_hook/$",
        views.PurchaseHook.as_view(),
        name="github_marketplace_purchase_hook",
    ),
    re_path(r"^install/$", views.Install.as_view(), name="github_marketplace_install"),
    re_path(
        r"^create/tenant/$",
        views.CreateTenant.as_view(),
        name="github_marketplace_create_tenant",
    ),
    re_path(
        r"^plans/$",
        views.ViewSubscriptionPlan.as_view(),
        name="github_marketplace_plans",
    ),
    re_path(r"^fastspring/$", views.FastSpringHook.as_view(), name="fastspring"),
]
