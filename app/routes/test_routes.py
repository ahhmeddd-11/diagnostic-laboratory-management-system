from flask import Blueprint, request, jsonify, session
from app.models.db import get_db_connection

test_bp = Blueprint('test', __name__)

def is_auth():
    return 'user_id' in session

@test_bp.route('/', methods=['GET'])
def get_tests():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Tests ORDER BY test_name ASC")
        tests = cursor.fetchall()
        
        cursor.execute("SELECT id, test_id, parameter_name, unit, normal_range, display_order, formula, parameter_type FROM Test_Parameters ORDER BY test_id, display_order ASC")
        all_params = cursor.fetchall()
        
        from collections import defaultdict
        params_by_test = defaultdict(list)
        for p in all_params:
            params_by_test[p['test_id']].append(p)
            
        for t in tests:
            t['price'] = float(t['price']) # Convert decimal to float
            t['created_at'] = str(t['created_at'])
            t['parameters'] = params_by_test.get(t['id'], [])
            
        return jsonify(tests)
    finally:
        cursor.close()
        conn.close()

@test_bp.route('/<int:id>/parameters', methods=['PUT'])
def update_test_parameters(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') not in ['Admin', 'Technician']:
        return jsonify({'error': 'Forbidden'}), 403
        
    data = request.json # List of parameters: [{name, unit, range, order, formula, type}, ...]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Clear existing parameters and re-insert (simpler than syncing)
        cursor.execute("DELETE FROM Test_Parameters WHERE test_id = %s", (id,))
        for p in data:
            cursor.execute("""
                INSERT INTO Test_Parameters (test_id, parameter_name, unit, normal_range, display_order, formula, parameter_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (id, p['parameter_name'], p['unit'], p['normal_range'], p.get('display_order', 0), p.get('formula'), p.get('parameter_type', 'text')))
            
        conn.commit()
        return jsonify({'message': 'Parameters updated successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@test_bp.route('/packages', methods=['GET'])
def get_packages():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Test_Packages ORDER BY package_name ASC")
        packages = cursor.fetchall()
        
        # Get tests for each package
        for p in packages:
            p['price'] = float(p['price'])
            p['created_at'] = str(p['created_at'])
            
            cursor.execute("""
                SELECT t.* FROM Tests t
                JOIN Test_Package_Tests pt ON t.id = pt.test_id
                WHERE pt.package_id = %s
            """, (p['id'],))
            p['tests'] = cursor.fetchall()
            for t in p['tests']:
                t['price'] = float(t['price'])
                
        return jsonify(packages)
    finally:
        cursor.close()
        conn.close()

@test_bp.route('/packages', methods=['POST'])
def add_package():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.json
    package_name = data.get('package_name')
    price = data.get('price')
    description = data.get('description', '')
    test_ids = data.get('test_ids', []) # List of test IDs
    
    if not package_name or price is None:
        return jsonify({'error': 'package_name and price are required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Test_Packages (package_name, price, description)
            VALUES (%s, %s, %s)
        """, (package_name, price, description))
        package_id = cursor.lastrowid
        
        for t_id in test_ids:
            cursor.execute("INSERT INTO Test_Package_Tests (package_id, test_id) VALUES (%s, %s)", (package_id, t_id))
            
        conn.commit()
        return jsonify({'message': 'Package created successfully', 'id': package_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@test_bp.route('/packages/<int:id>', methods=['DELETE'])
def delete_package(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Forbidden'}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Test_Packages WHERE id = %s", (id,))
        conn.commit()
        return jsonify({'message': 'Package deleted successfully'})
    finally:
        cursor.close()
        conn.close()

@test_bp.route('/', methods=['POST'])
def add_test():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') not in ['Admin', 'Technician']:
        return jsonify({'error': 'Forbidden'}), 403
        
    data = request.json
    required = ['test_name', 'normal_range', 'price']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Tests (test_name, normal_range, price)
            VALUES (%s, %s, %s)
        """, (data['test_name'], data['normal_range'], data['price']))
        conn.commit()
        return jsonify({'message': 'Test added successfully', 'id': cursor.lastrowid}), 201
    finally:
        cursor.close()
        conn.close()

@test_bp.route('/<int:id>', methods=['PUT'])
def update_test(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') not in ['Admin', 'Technician']:
        return jsonify({'error': 'Forbidden'}), 403
        
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Tests SET test_name=%s, normal_range=%s, price=%s
            WHERE id=%s
        """, (data['test_name'], data['normal_range'], data['price'], id))
        conn.commit()
        return jsonify({'message': 'Test updated successfully'})
    finally:
        cursor.close()
        conn.close()

@test_bp.route('/<int:id>', methods=['DELETE'])
def delete_test(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Forbidden'}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Tests WHERE id = %s", (id,))
        conn.commit()
        return jsonify({'message': 'Test deleted successfully'})
    finally:
        cursor.close()
        conn.close()


