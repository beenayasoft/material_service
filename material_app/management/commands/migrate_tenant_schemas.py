from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Applique les migrations à tous les schémas de tenants (multi-tenant)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Recherche des schémas tenants...'))
        tenant_schemas = self._get_tenant_schemas()
        if not tenant_schemas:
            self.stdout.write(self.style.WARNING('Aucun schéma tenant trouvé.'))
            return
        for schema in tenant_schemas:
            self.stdout.write(self.style.NOTICE(f'Application des migrations pour le schéma : {schema}'))
            self._migrate_schema(schema)
        self.stdout.write(self.style.SUCCESS('Migrations terminées pour tous les tenants.'))

    def _get_tenant_schemas(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name FROM information_schema.schemata
                WHERE schema_name LIKE 'tenant_%'
            """)
            return [row[0] for row in cursor.fetchall()]

    def _migrate_schema(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name},public")
        call_command('migrate', verbosity=0)
        # Remettre le schéma sur public après migration
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public") 