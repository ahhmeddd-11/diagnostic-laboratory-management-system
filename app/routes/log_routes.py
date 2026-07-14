from flask import Blueprint, request, jsonify, session
from app.models.db import get_db_connection

log_bp = Blueprint('logs', __name__)

def is_auth():
    return 'user_id' in session

@log_bp.route('/', methods=['POST'])
def add_log():
    data = request.json
    action_type = data.get('action_type', 'UNKNOWN')
    description = data.get('description', '')
    
    # We grab user info from session if available
    user_id = session.get('user_id')
    user_name = session.get('name')
    
    # Handle explicit login failed/success logs where session might not be set yet,
    # or passed explicitly from auth.js before session is finalized.
    if data.get('user_name'):
        user_name = data.get('user_name')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ActivityLogs (user_id, user_name, action_type, description)
            VALUES (%s, %s, %s, %s)
        """, (user_id, user_name, action_type, description))
        conn.commit()
        return jsonify({'message': 'Logged successfully'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@log_bp.route('/', methods=['GET'])
def get_logs():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Forbidden'}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get latest 200 logs
        cursor.execute("SELECT * FROM ActivityLogs ORDER BY created_at DESC LIMIT 200")
        logs = cursor.fetchall()
        for log in logs:
            log['created_at'] = str(log['created_at'])
        return jsonify(logs)
    finally:
        cursor.close()
        conn.close()
