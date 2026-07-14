import os
import json
# pyrefly: ignore [missing-import]
import mysql.connector
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from config import Config
import sys

setup_bp = Blueprint('setup', __name__)

@setup_bp.route('/initialize', methods=['POST'])
def initialize_setup():
    if Config.IS_CONFIGURED:
        return jsonify({'error': 'System is already configured'}), 400
        
    data = request.json
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
        return jsonify({'error': f"Failed to connect to MySQL: {str(e)}"}), 400
        
    # 2. Save Configuration locally
    try:
        app_data_dir = os.getenv('APPDATA')
        if not app_data_dir:
            app_data_dir = os.path.expanduser('~')
        config_dir = os.path.join(app_data_dir, 'UnilabDiagnostics')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        config_path = os.path.join(config_dir, 'db_config.json')
        with open(config_path, 'w') as f:
            json.dump({
                'host': host,
                'user': user,
                'password': password,
                'database': database
            }, f, indent=4)
            
        # Update config in memory
        Config.MYSQL_HOST = host
        Config.MYSQL_USER = user
        Config.MYSQL_PASSWORD = password
        Config.MYSQL_DB = database
    except Exception as e:
        return jsonify({'error': f"Failed to save configuration: {str(e)}"}), 500
        
    # 3. Build Tables & Seed Data
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        
        # Execute schema
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            # app/routes/setup_routes.py -> app/routes -> app -> root
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            
        schema_path = os.path.join(base_dir, 'database', 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            for statement in sql_script.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            conn.commit()
        else:
            raise Exception(f"CRITICAL ERROR: schema.sql file not found at {schema_path}. The database cannot be built.")
            
        # Add Admin
        cursor.execute("SELECT * FROM Users WHERE email = 'admin@lab.com'")
        if not cursor.fetchone():
            hashed_pw = generate_password_hash("admin123")
            cursor.execute("""
                INSERT INTO Users (name, email, password, role, branch_id)
                VALUES (%s, %s, %s, %s, %s)
            """, ("System Admin", "admin@lab.com", hashed_pw, "Admin", 1))
            conn.commit()
            
        # Seed Tests
        tests_file = os.path.join(base_dir, 'bulk_reports', 'extracted_tests.json')
        if os.path.exists(tests_file):
            with open(tests_file, 'r', encoding='utf-8') as f:
                tests_data = json.load(f)
                
            cursor.execute("SELECT COUNT(*) FROM Tests")
            count = cursor.fetchone()[0]
            if count == 0:
                for test_name, parameters in tests_data.items():
                    cursor.execute("""
                        INSERT INTO Tests (test_name, normal_range, price)
                        VALUES (%s, %s, %s)
                    """, (test_name, 'Refer to Report', 0.00))
                    test_id = cursor.lastrowid
                    
                    for idx, param in enumerate(parameters):
                        cursor.execute("""
                            INSERT INTO Test_Parameters (test_id, parameter_name, unit, normal_range, display_order)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            test_id,
                            param.get('name', '')[:100],
                            param.get('unit', '')[:50],
                            param.get('normal_range', '')[:100],
                            idx
                        ))
                conn.commit()
                
        cursor.close()
        conn.close()
        
        # Mark as configured
        Config.IS_CONFIGURED = True
        
        return jsonify({'message': 'Setup completed successfully!'})
        
    except Exception as e:
        # Revert config if failed
        Config.IS_CONFIGURED = False
        return jsonify({'error': f"Database initialization failed: {str(e)}"}), 500
