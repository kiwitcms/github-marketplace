# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import uuid
from datetime import datetime, timedelta, timezone as datetime_timezone

from django.db import connection
from django.test import TestCase
from django.utils import timezone

from tcms_github_marketplace.models import ReadOnlyDatabaseRole


class ReadOnlyDatabaseRoleTestCase(TestCase):
    valid_until = datetime(2026, 2, 1, 23, 59, 59, tzinfo=datetime_timezone.utc)

    def setUp(self):
        super().setUp()

        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA ro_test")
            cursor.execute("CREATE TABLE ro_test.some_table (id integer)")

    def assert_role_exists(self, name):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT rolvaliduntil FROM pg_roles WHERE rolname = %s", [name]
            )
            role = cursor.fetchone()

        self.assertIsNotNone(role)
        self.assertIsNotNone(role[0])

    def assert_read_only(self, name):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT has_schema_privilege(%s, %s, 'USAGE')", [name, "ro_test"]
            )
            self.assertTrue(cursor.fetchone()[0])

            for privilege in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
                cursor.execute(
                    "SELECT has_table_privilege(%s, %s, %s)",
                    [name, "ro_test.some_table", privilege],
                )
                self.assertEqual(cursor.fetchone()[0], privilege == "SELECT")

    def test_create_for_schema(self):
        role = ReadOnlyDatabaseRole.create_for_schema("ro_test", self.valid_until)

        self.assertEqual(role.name, "ro_for_ro_test")
        self.assertIsNotNone(role.created_at)
        # password is a generated UUID
        self.assertEqual(role.password, str(uuid.UUID(role.password)))
        self.assertEqual(role.valid_until, self.valid_until)
        # model record is stored
        self.assertTrue(ReadOnlyDatabaseRole.objects.filter(pk=role.pk).exists())
        # actual DB role exists & is read-only
        self.assert_role_exists(role.name)
        self.assert_read_only(role.name)

    def test_update_valid_until(self):
        role = ReadOnlyDatabaseRole.create_for_schema("ro_test", self.valid_until)

        valid_until = timezone.now() + timedelta(days=366)
        role.update_valid_until(valid_until)

        role.refresh_from_db()
        self.assertEqual(role.valid_until, valid_until)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT rolvaliduntil FROM pg_roles WHERE rolname = %s", [role.name]
            )
            self.assertEqual(cursor.fetchone()[0], valid_until)
