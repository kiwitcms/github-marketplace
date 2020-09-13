# Copyright (c) 2019-2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.urls import re_path
from tcms_github_marketplace import views


urlpatterns = [
    re_path(r'^purchase_hook/$', views.PurchaseHook.as_view(),
            name='github_marketplace_purchase_hook'),
    re_path(r'^install/$', views.Install.as_view(), name='github_marketplace_install'),
    re_path(r'^create/tenant/$', views.CreateTenant.as_view(),
            name='github_marketplace_create_tenant'),
    re_path(r'^plans/$', views.ViewSubscriptionPlan.as_view(), name='github_marketplace_plans'),
    re_path(r'^fastspring/$', views.FastSpringHook.as_view(), name='fastspring'),
]
