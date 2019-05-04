# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.contrib import admin
from django.conf.urls import include, url

from tcms_github_marketplace import urls as marketplace_urls

from test_project import views


urlpatterns = [
    url(r'^$', views.index),  # needed b/c testing can't resolve redirects
    url(r'^github/marketplace/', include(marketplace_urls)),

    # only for testing purposes
    url(r'^admin/', admin.site.urls),
]
