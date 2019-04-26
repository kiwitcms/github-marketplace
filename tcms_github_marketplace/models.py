# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex


class Purchase(models.Model):
    """
        Holds information about GitHub ``marketplace_purchase`` events:
        https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/github-marketplace-webhook-events/
    """
    action = models.CharField(max_length=64, db_index=True)
    sender = models.CharField(max_length=64, db_index=True)
    effective_date = models.DateTimeField(db_index=True)

    # this is for internal purposes
    received_on = models.DateTimeField(db_index=True, auto_now_add=True)

    marketplace_purchase = JSONField()

    class Meta:
        indexes = [
            GinIndex(fastupdate=False,
                     fields=['marketplace_purchase']),
        ]

    def __str__(self):
        return "Purchase %s from %s on %s" % (self.action,
                                              self.sender,
                                              self.received_on.isoformat())
