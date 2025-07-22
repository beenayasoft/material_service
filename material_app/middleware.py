from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.db import connection, ProgrammingError

class TenantSchemaMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer le schéma PostgreSQL en fonction du tenant_id passé dans l'en-tête HTTP X-TENANT-ID.
    Exige la présence du header, retourne 400 si absent.
    Utilise ce header pour le multi-tenant (création/bascule schéma).
    Attache aussi X-User-ID à la requête pour audit/sécurité (optionnel).
    """
    def process_request(self, request):
        tenant_id = request.META.get('HTTP_X_TENANT_ID')
        if not tenant_id:
            return JsonResponse({'error': 'X-TENANT-ID header required'}, status=400)
        schema_name = f"tenant_{tenant_id.replace('-', '_')}"
        if not self._schema_exists(schema_name):
            self._create_tenant_schema(schema_name)
        self._set_schema(schema_name)
        # Attacher X-User-ID à la requête si présent (optionnel)
        
        #--------
        user_id = request.META.get('HTTP_X_USER_ID')
        if user_id:
            request.user_id = user_id
        #--------

    def process_response(self, request, response):
        self._set_schema('public')
        return response

    def _set_schema(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name},public")

    def _schema_exists(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s", [schema_name])
            return cursor.fetchone() is not None

    def _create_tenant_schema(self, schema_name):
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name}')
        except ProgrammingError:
            pass
