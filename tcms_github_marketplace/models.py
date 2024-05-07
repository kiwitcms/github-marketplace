# Copyright (c) 2019-2024 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.db import models
from django.contrib.postgres.indexes import GinIndex


class ManualPurchase(models.Model):  # pylint: disable=remove-empty-class
    """
    A model class without any fields which is needed in order to
    generate an admin page. The admin page will be used to record
    manual purchases which will be processed on the fly and recorded
    inside the standard Purchase model.
    """


@models.CharField.register_lookup
class IPrefixFor(models.lookups.StartsWith):  # pylint: disable=abstract-method
    """
    The reverse of ``_startswith``. Selects records where the
    DB column value acts as a prefix for the supplied lookup argument!
    https://dba.stackexchange.com/a/149632

    SELECT * FROM my_table WHERE 'value' ILIKE model_field || '%';


    .. warning::

        We achieve the results by swapping the left-hand and right-hand side operators
        for a regular PatternLookup, e.g IStartsWith
    """

    lookup_name = "iprefix_for"
    param_pattern = "%s"

    # WARNING: internally process the other side of the expression
    def process_lhs(self, compiler, connection, lhs=None):
        return super().process_rhs(compiler, connection)

    # WARNING: internally process the other side of the expression
    def process_rhs(self, qn, connection):
        return super().process_lhs(qn, connection)

    def get_rhs_op(self, connection, rhs):
        # WARNING: Postgresql specific
        return f"ILIKE {rhs}::text || '%%'"


class Purchase(models.Model):
    """
    Holds information about GitHub ``marketplace_purchase`` events:
    https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/github-marketplace-webhook-events/
    """

    vendor = models.CharField(max_length=16, db_index=True, blank=True, null=True)
    action = models.CharField(max_length=64, db_index=True)
    sender = models.EmailField(db_index=True)
    subscription = models.CharField(max_length=32, db_index=True, blank=True, null=True)
    effective_date = models.DateTimeField(db_index=True)
    should_have_tenant = models.BooleanField(default=False, db_index=True)
    should_have_support = models.BooleanField(default=False, db_index=True)
    gitops_prefix = models.CharField(
        null=True, blank=True, db_index=True, max_length=256
    )

    # this is for internal purposes
    received_on = models.DateTimeField(db_index=True, auto_now_add=True)

    payload = models.JSONField()

    class Meta:
        indexes = [
            GinIndex(
                fastupdate=False, fields=["payload"], name="tcms_github_payload_gin"
            ),
        ]

    def __str__(self):
        return f"Purchase {self.action} from {self.sender} on {self.received_on.isoformat()}"
