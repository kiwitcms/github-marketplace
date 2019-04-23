# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.db import models
from django.conf import settings


class Purchase(models.Model):
# TODO: fix these
    name = models.CharField(max_length=100, db_index=True)
    created_on = models.DateField(auto_now_add=True, db_index=True)
    paid_until = models.DateField(null=True, blank=True, db_index=True)
    on_trial = models.BooleanField(default=True, db_index=True)
    authorized_users = models.ManyToManyField(to=settings.AUTH_USER_MODEL)
