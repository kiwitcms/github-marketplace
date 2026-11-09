# Copyright (c) 2019-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import uuid
from datetime import datetime

import django.db
from django.db import models, transaction
from django.contrib.postgres.indexes import GinIndex
from psycopg import sql


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

    @staticmethod
    def next_billing_date_from(payload):
        next_billing_date = None

        # a GitHub Marketplace subscription
        if "next_billing_date" in payload["marketplace_purchase"]:
            next_billing_date = payload["marketplace_purchase"]["next_billing_date"]

        if next_billing_date is None:
            return None

        # GitHub uses the "2024-10-16T00:00:00Z" or "2024-10-16T00:00:00+00:00" format
        # so we drop the timezone portion b/c our server is configured in UTC
        return datetime.strptime(next_billing_date[:19], "%Y-%m-%dT%H:%M:%S")

    @property
    def next_billing_date(self):
        return self.next_billing_date_from(self.payload)

    @property
    def unit_count(self):  # pylint: disable=too-many-return-statements
        """
        A value of zero/0 represent a case where the code wasn't able to find
        the actual value from the event payload!
        """
        if self.vendor in ("github", "github_cron"):
            if "marketplace_purchase" not in self.payload:
                return 0

            return self.payload["marketplace_purchase"].get("unit_count", 0)

        if self.vendor == "manual_purchase":
            return self.payload["marketplace_purchase"].get("unit_count", 0)

        if self.vendor == "fastspring":
            # Kiwi TCMS Partner Store
            if "items" in self.payload:
                return self.payload["items"][0].get("quantity", 0)

            # FastSpring direct sale
            if "data" not in self.payload:
                return 0

            value = self.payload["data"].get("quantity", 0)
            if value == 0 and "subscription" in self.payload["data"]:
                value = self.payload["data"]["subscription"].get("quantity", 0)

            if value == 0 and "items" in self.payload["data"]:
                value = self.payload["data"]["items"][0].get("quantity", 0)

            return value

        return 0


class PrivateRepoToken(models.Model):
    vendor = models.CharField(max_length=16, db_index=True)
    subscription = models.CharField(max_length=32, db_index=True, blank=True, null=True)
    created_at = models.DateTimeField(db_index=True, auto_now_add=True)
    payload = models.JSONField()

    class Meta:
        indexes = [
            GinIndex(
                fastupdate=False, fields=["payload"], name="ghmp_privaterepotoken_gin"
            ),
        ]

    @property
    def token(self):
        return self.payload["token_value"]


class ReadOnlyDatabaseRole(models.Model):
    READ_ONLY_ROLE_PREFIX = "ro_for_"

    name = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(db_index=True, auto_now_add=True)
    valid_until = models.DateTimeField(db_index=True)
    password = models.CharField(max_length=36)

    def __str__(self):
        return self.name

    @classmethod
    def create_for_schema(cls, schema_name, valid_until):
        with transaction.atomic():
            instance = cls(
                name=f"{cls.READ_ONLY_ROLE_PREFIX}{schema_name}",
                password=str(uuid.uuid4()),
                valid_until=valid_until,
            )
            instance.save()
            instance.create_database_role(schema_name)

        return instance

    def create_database_role(self, schema_name):
        # WARNING: all values are escaped via psycopg's Identifier/Literal
        # wrappers to prevent SQL injection!
        with django.db.connection.cursor() as cursor:
            schema = sql.Identifier(schema_name)
            role = sql.Identifier(self.name)

            cursor.execute(
                sql.SQL("""
                    CREATE ROLE {name} WITH LOGIN ENCRYPTED PASSWORD {password} VALID UNTIL {valid_until};
                    GRANT USAGE ON SCHEMA {schema} TO {name};
                    GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {name};
                    -- cover tables which are created after this call
                    ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {name};
                    """).format(
                    name=role,
                    password=sql.Literal(self.password),
                    valid_until=sql.Literal(self.valid_until.isoformat()),
                    schema=schema,
                )
            )

    def update_valid_until(self, valid_until):
        with transaction.atomic():
            self.valid_until = valid_until
            self.save()

            with django.db.connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("ALTER ROLE {name} VALID UNTIL {valid_until}").format(
                        name=sql.Identifier(self.name),
                        valid_until=sql.Literal(self.valid_until.isoformat()),
                    )
                )
