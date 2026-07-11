import mysql.connector
import json
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def migrate_and_seed():
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )
    cursor = conn.cursor()
    
    print("Applying schema updates...")
    try:
        # Add branch_id to Users if it doesn't exist
        cursor.execute("SHOW COLUMNS FROM Users LIKE 'branch_id'")
        if not cursor.fetchone():
            print("Adding branch_id to Users table...")
            cursor.execute("ALTER TABLE Users ADD COLUMN branch_id INT DEFAULT 1")
    except Exception as e:
        print(f"Error checking/adding branch_id: {e}")
        
    # Create new tables
    tables = [
        """
        CREATE TABLE IF NOT EXISTS Test_Parameters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            test_id INT NOT NULL,
            parameter_name VARCHAR(100) NOT NULL,
            unit VARCHAR(50) DEFAULT '',
            normal_range VARCHAR(100) DEFAULT '',
            display_order INT DEFAULT 0,
            formula TEXT DEFAULT NULL,
            parameter_type VARCHAR(50) DEFAULT 'text',
            FOREIGN KEY (test_id) REFERENCES Tests(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Test_Packages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            package_name VARCHAR(100) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Test_Package_Tests (
            package_id INT NOT NULL,
            test_id INT NOT NULL,
            PRIMARY KEY (package_id, test_id),
            FOREIGN KEY (package_id) REFERENCES Test_Packages(id) ON DELETE CASCADE,
            FOREIGN KEY (test_id) REFERENCES Tests(id) ON DELETE CASCADE
        )
        """
    ]
    for sql in tables:
        try:
            cursor.execute(sql)
        except Exception as e:
            print(f"Error creating table: {e}")
            
    # Seed 176 Tests
    tests_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bulk_reports', 'extracted_tests.json')
    if os.path.exists(tests_file):
        print("Seeding tests from extracted_tests.json...")
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
        print(f"File not found: {tests_file}")
        
    conn.commit()
    cursor.close()
    conn.close()
    print("Migration and seeding completed successfully.")

if __name__ == '__main__':
    migrate_and_seed()
