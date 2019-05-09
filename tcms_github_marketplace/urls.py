# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.conf.urls import url
from tcms_github_marketplace import views


urlpatterns = [
    url(r'^purchase_hook/$', views.PurchaseHook.as_view(), name='github_marketplace_purchase_hook'),
    url(r'^install/$', views.Install.as_view(), name='github_marketplace_install'),
    url(r'^create/tenant/$', views.CreateTenant.as_view(), name='github_marketplace_create_tenant'),
    url(r'^plans/$', views.ViewSubscriptionPlan.as_view(), name='github_marketplace_plans'),
]
