"""
Test custom django management commands
"""
# mock behaviour of db
from unittest.mock import patch

# possible error when connecting to db
from psycopg2 import OperationalError as Psycopg2Error

# call cmd testing by its name
from django.core.management import call_command

from django.db.utils import OperationalError

# testing unitest - simpletestcase since no creating db
from django.test import SimpleTestCase

# decorator to mock behaviour
@patch('core.management.commands.wait_for_db.Command.check')
class CommandTest(SimpleTestCase):
    """Test commands."""

    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for db when db is ready."""
        patched_check.return_value = True

        call_command('wait_for_db')

        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test waiting for db with delays."""
        patched_check.side_effect = [Psycopg2Error] * 2 + \
            [OperationalError] * 3 + [True]

        call_command('wait_for_db')
        # 3 + 2 + true-v
        self.assertEqual(patched_check.call_count, 6)

        patched_check.assert_called_with(databases=['default'])