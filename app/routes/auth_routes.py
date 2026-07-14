import os
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app.models.db import get_db_connection

UPLOAD_FOLDER = 'static/uploads/profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            session['branch_id'] = user.get('branch_id', 1)
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'role': user['role'],
                    'branch_id': user.get('branch_id', 1),
                    'profile_photo': user.get('profile_photo')
                }
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        cursor.close()
        conn.close()

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/me', methods=['GET'])
def get_me():
    if 'user_id' in session:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id, name, role, profile_photo, branch_id FROM Users WHERE id = %s", (session['user_id'],))
                user = cursor.fetchone()
                if user:
                    return jsonify({'user': user})
            finally:
                cursor.close()
                conn.close()
                
        return jsonify({
            'user': {
                'id': session['user_id'],
                'name': session.get('name'),
                'role': session.get('role'),
                'branch_id': session.get('branch_id', 1)
            }
        })
    return jsonify({'error': 'Not authenticated'}), 401

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': 'Old and new passwords required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT password FROM Users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password'], old_password):
            return jsonify({'error': 'Incorrect old password'}), 401
            
        hashed_pw = generate_password_hash(new_password)
        cursor.execute("UPDATE Users SET password = %s WHERE id = %s", (hashed_pw, session['user_id']))
        conn.commit()
        
        return jsonify({'message': 'Password changed successfully'})
    finally:
        cursor.close()
        conn.close()

@auth_bp.route('/profile-photo', methods=['POST'])
def upload_profile_photo():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    if 'photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        # Create directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Generate safe unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"user_{session['user_id']}_{os.urandom(4).hex()}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        file.save(filepath)
        
        # Update database
        photo_url = f"/static/uploads/profiles/{filename}"
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # First, fetch old photo to delete it
            cursor.execute("SELECT profile_photo FROM Users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
            if user and user.get('profile_photo'):
                old_path = user['profile_photo'].lstrip('/') # remove leading slash
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass # Ignore if file missing or locked
            
            cursor.execute("UPDATE Users SET profile_photo = %s WHERE id = %s", (photo_url, session['user_id']))
            conn.commit()
            return jsonify({'message': 'Photo uploaded successfully', 'photo_url': photo_url})
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'error': 'Invalid file type'}), 400

@auth_bp.route('/profile-photo', methods=['DELETE'])
def remove_profile_photo():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT profile_photo FROM Users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        if user and user.get('profile_photo'):
            old_path = user['profile_photo'].lstrip('/')
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass
                    
            cursor.execute("UPDATE Users SET profile_photo = NULL WHERE id = %s", (session['user_id'],))
            conn.commit()
            
        return jsonify({'message': 'Photo removed successfully'})
    finally:
        cursor.close()
        conn.close()
