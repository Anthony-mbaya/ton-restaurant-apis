"""
Django command to wait for database to be available
"""
# used in sleep
import time
# psycopg2 error when db not ready
from psycopg2 import OperationalError as Psycopg2OpError
# django error when db not ready
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Wait for database to be available"""
    def handle(self, *args, **options):
        """Wait for database to be available"""
        self.stdout.write('PLease wait for db to start...') # log text on screen as cmd is executed
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default']) # called and db not ready go to except
                db_up = True
            except(Psycopg2OpError, OperationalError):
                self.stdout.write('Be humble eh! 1 sec please...')
                time.sleep(1) # wait 1 second before checking again

        self.stdout.write(self.style.SUCCESS('Woo-hoo congrats db available!'))