import os
import json
import sys
import mysql.connector
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db import connections, connection
from werkzeug.security import generate_password_hash
from accounts.models import User
from .models import ActivityLog

def is_auth(request):
    return request.user.is_authenticated

def get_role(request):
    return request.user.role if request.user.is_authenticated else None

@csrf_exempt
@require_http_methods(["GET", "POST"])
def log_list_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        action_type = data.get('action_type', 'UNKNOWN')
        description = data.get('description', '')

        # Grab user info natively
        user_id = None
        user_name = None
        if request.user.is_authenticated:
            user_id = request.user.id
            user_name = request.user.name

        # Handle explicit override logs
        if data.get('user_name'):
            user_name = data.get('user_name')

        try:
            log = ActivityLog.objects.create(
                user_id=user_id,
                user_name=user_name,
                action_type=action_type,
                description=description
            )
            return JsonResponse({'message': 'Logged successfully', 'id': log.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == "GET":
        if not is_auth(request):
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        if get_role(request) != 'Admin':
            return JsonResponse({'error': 'Forbidden'}, status=403)

        logs = ActivityLog.objects.all().order_by('-created_at')[:200]
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'user_id': log.user_id,
                'user_name': log.user_name,
                'action_type': log.action_type,
                'description': log.description,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else ''
            })
        return JsonResponse(data, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def initialize_setup(request):
    if getattr(settings, 'IS_CONFIGURED', False):
        return JsonResponse({'error': 'System is already configured'}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    host = data.get('host', 'localhost')
    user = data.get('user', 'root')
    password = data.get('password', '')
    database = data.get('database', 'diagnostic_lab')

    # 1. Test Connection & Create Database
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return JsonResponse({'error': f"Failed to connect to MySQL: {str(e)}"}, status=400)

    # 2. Save Configuration locally
    try:
        app_data_dir = os.getenv('APPDATA') or os.path.expanduser('~')
        config_dir = os.path.join(app_data_dir, 'UnilabDiagnostics')
        os.makedirs(config_dir, exist_ok=True)

        config_path = os.path.join(config_dir, 'db_config.json')
        with open(config_path, 'w') as f:
            json.dump({
                'host': host,
                'user': user,
                'password': password,
                'database': database
            }, f, indent=4)

        # Update core settings in-memory
        settings.DATABASES['default']['HOST'] = host
        settings.DATABASES['default']['USER'] = user
        settings.DATABASES['default']['PASSWORD'] = password
        settings.DATABASES['default']['NAME'] = database
        
        # Close connection to force Django to reconnect
        connections['default'].close()
    except Exception as e:
        return JsonResponse({'error': f"Failed to save configuration: {str(e)}"}, status=500)

    # 3. Build Tables & Seed Data using connection cursor
    try:
        schema_path = os.path.join(settings.BASE_DIR, 'database', 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            with connection.cursor() as db_cursor:
                for statement in sql_script.split(';'):
                    if statement.strip():
                        db_cursor.execute(statement)
        else:
            raise Exception(f"CRITICAL ERROR: schema.sql file not found at {schema_path}.")

        # Add Default Admin if not exists
        admin_exists = User.objects.filter(email='admin@lab.com').exists()
        if not admin_exists:
            hashed_pw = generate_password_hash("admin123")
            User.objects.create(
                name="System Admin",
                email="admin@lab.com",
                password=hashed_pw,
                role="Admin",
                branch_id=1
            )

        # Seed Tests
        tests_file = os.path.join(settings.BASE_DIR, 'bulk_reports', 'extracted_tests.json')
        if os.path.exists(tests_file):
            with open(tests_file, 'r', encoding='utf-8') as f:
                tests_data = json.load(f)

            from tests.models import Test, TestParameter
            if Test.objects.count() == 0:
                for test_name, parameters in tests_data.items():
                    test = Test.objects.create(
                        test_name=test_name,
                        normal_range='Refer to Report',
                        price=0.00
                    )
                    for idx, param in enumerate(parameters):
                        TestParameter.objects.create(
                            test=test,
                            parameter_name=param.get('name', '')[:100],
                            unit=param.get('unit', '')[:50],
                            normal_range=param.get('normal_range', '')[:100],
                            display_order=idx
                        )

        # Mark configured
        settings.IS_CONFIGURED = True
        return JsonResponse({'message': 'Setup completed successfully!'})

    except Exception as e:
        settings.IS_CONFIGURED = False
        return JsonResponse({'error': f"Database initialization failed: {str(e)}"}, status=500)
