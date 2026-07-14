import mysql.connector
from werkzeug.security import generate_password_hash
from config import Config
import os
import json

def init_db():
    print("Connecting to MySQL server...")
    try:
        # Connect without DB first to create it
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
        conn.commit()
        cursor.close()
        conn.close()
        
        # Now connect to the created DB to seed data
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor()

        # Read and execute schema
        schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
        if os.path.exists(schema_path):
            print("Executing schema.sql...")
            with open(schema_path, 'r') as f:
                sql_script = f.read()
                
            statements = sql_script.split(';')
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            conn.commit()
        else:
            print("schema.sql not found!")

        # Seed Admin user if not exists
        cursor.execute("SELECT * FROM Users WHERE email = 'admin@lab.com'")
        if not cursor.fetchone():
            hashed_pw = generate_password_hash("admin123")
            cursor.execute("""
                INSERT INTO Users (name, email, password, role, branch_id)
                VALUES (%s, %s, %s, %s, %s)
            """, ("System Admin", "admin@lab.com", hashed_pw, "Admin", 1))
            conn.commit()
            print("Default admin created: admin@lab.com / admin123")
        else:
            print("Admin user already exists.")
            
        # Seed Tests
        tests_file = os.path.join(os.path.dirname(__file__), 'bulk_reports', 'extracted_tests.json')
        if os.path.exists(tests_file):
            print("Seeding default tests...")
            with open(tests_file, 'r', encoding='utf-8') as f:
                tests_data = json.load(f)
                
            cursor.execute("SELECT COUNT(*) FROM Tests")
            count = cursor.fetchone()[0]
            
            if count == 0:
                for test_name, parameters in tests_data.items():
                    # Insert test
                    cursor.execute("""
                        INSERT INTO Tests (test_name, normal_range, price)
                        VALUES (%s, %s, %s)
                    """, (test_name, 'Refer to Report', 0.00))
                    test_id = cursor.lastrowid
                    
                    # Insert parameters
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
                print(f"Successfully seeded {len(tests_data)} tests and their parameters.")
            else:
                print(f"Tests already seeded (found {count} tests).")
        else:
            print(f"Tests file not found: {tests_file}")

        cursor.close()
        conn.close()
        print("Database initialization complete.")
        
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == '__main__':
    init_db()
