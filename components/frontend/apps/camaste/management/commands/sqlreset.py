from optparse import make_option
from django.core.management.base import BaseCommand, AppCommand, CommandError
from django.core.management.color import no_style
from django.db import connections, transaction, DEFAULT_DB_ALIAS

# Inspired by https://github.com/gregmuellegger/django-reset/

class Command(AppCommand):
    option_list = AppCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to reset. '
                'Defaults to the "default" database.'),
    )
    help = "Executes ``sqlreset`` for the given app(s) in the current database."
    args = '[appname ...]'

    output_transaction = True

    def handle(self, **options):
        using = options.get('database')
        connection = connections[using]

        db_name = connection.settings_dict['NAME']

        if connection.vendor == 'mongoengine':
            cursor = connection.create_cursor()
            print("Dropping Mongo database '%s'.." % ( db_name, ))
            cursor.drop_database(db_name)

        elif connection.vendor == 'mysql':
            cursor = connection.cursor()
            cursor.execute('show tables;')
            print("Dropping all tables..")
            parts = ('DROP TABLE IF EXISTS %s;' % table for (table,) in cursor.fetchall())
            sql = 'SET FOREIGN_KEY_CHECKS = 0;\n' + '\n'.join(parts) + 'SET FOREIGN_KEY_CHECKS = 1;\n'
            connection.cursor().execute(sql)

        else:
            raise Exception, "reset not supported on backend '%s'" % ( connection.vendor, )


