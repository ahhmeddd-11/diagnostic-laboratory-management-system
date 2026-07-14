from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from app.models.db import get_db_connection

user_bp = Blueprint('user', __name__)

def is_auth():
    return 'user_id' in session

def is_admin():
    return session.get('role') == 'Admin'

@user_bp.route('/', methods=['GET'])
def get_users():
    if not is_auth() or not is_admin():
        return jsonify({'error': 'Forbidden'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, name, email, role, branch_id, created_at 
            FROM Users 
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        for u in users:
            u['created_at'] = str(u['created_at'])
        return jsonify(users)
    finally:
        cursor.close()
        conn.close()

@user_bp.route('/', methods=['POST'])
def create_user():
    if not is_auth() or not is_admin():
        return jsonify({'error': 'Forbidden'}), 403
        
    data = request.json
    required = ['name', 'email', 'password', 'role']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
        
    if data['role'] not in ['Admin', 'Technician', 'Operator']:
        return jsonify({'error': 'Invalid role'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed_pw = generate_password_hash(data['password'])
        branch_id = data.get('branch_id', 1)
        cursor.execute("""
            INSERT INTO Users (name, email, password, role, branch_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['name'], data['email'], hashed_pw, data['role'], branch_id))
        conn.commit()
        return jsonify({'message': 'User created successfully', 'id': cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@user_bp.route('/<int:id>', methods=['DELETE'])
def delete_user(id):
    if not is_auth() or not is_admin():
        return jsonify({'error': 'Forbidden'}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Users WHERE id = %s", (id,))
        conn.commit()
        return jsonify({'message': 'User deleted successfully'})
    finally:
        cursor.close()
        conn.close()
