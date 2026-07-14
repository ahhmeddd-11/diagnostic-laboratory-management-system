from flask import Blueprint, request, jsonify, session
from app.models.db import get_db_connection

patient_bp = Blueprint('patient', __name__)

def is_auth():
    return 'user_id' in session

@patient_bp.route('/', methods=['GET'])
def get_patients():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if session.get('role') == 'Admin':
            cursor.execute("SELECT * FROM Patients ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM Patients ORDER BY id DESC")
        patients = cursor.fetchall()
        # Convert date to string for JSON serialization
        for p in patients:
            p['date'] = str(p['date'])
            p['created_at'] = str(p['created_at'])
        return jsonify(patients)
    finally:
        cursor.close()
        conn.close()

@patient_bp.route('/<int:id>', methods=['GET'])
def get_patient(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if session.get('role') == 'Admin':
            cursor.execute("SELECT * FROM Patients WHERE id = %s", (id,))
        else:
            cursor.execute("SELECT * FROM Patients WHERE id = %s", (id,))
        patient = cursor.fetchone()
        if patient:
            patient['date'] = str(patient['date'])
            patient['created_at'] = str(patient['created_at'])
            return jsonify(patient)
        return jsonify({'error': 'Patient not found'}), 404
    finally:
        cursor.close()
        conn.close()

@patient_bp.route('/', methods=['POST'])
def add_patient():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') not in ['Admin', 'Operator']:
        return jsonify({'error': 'Forbidden'}), 403
        
    data = request.json
    required = ['name', 'age', 'gender', 'date']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Patients (name, age, gender, date, referred_doctor)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['name'], data['age'], data['gender'], data['date'], data.get('referred_doctor')))
        conn.commit()
        return jsonify({'message': 'Patient added successfully', 'id': cursor.lastrowid}), 201
    finally:
        cursor.close()
        conn.close()

@patient_bp.route('/<int:id>', methods=['PUT'])
def update_patient(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') not in ['Admin', 'Operator']:
        return jsonify({'error': 'Forbidden'}), 403
        
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Patients SET name=%s, age=%s, gender=%s, date=%s, referred_doctor=%s
            WHERE id=%s
        """, (data['name'], data['age'], data['gender'], data['date'], data.get('referred_doctor'), id))
        conn.commit()
        return jsonify({'message': 'Patient updated successfully'})
    finally:
        cursor.close()
        conn.close()

@patient_bp.route('/<int:id>', methods=['DELETE'])
def delete_patient(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Forbidden'}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Patients WHERE id = %s", (id,))
        conn.commit()
        return jsonify({'message': 'Patient deleted successfully'})
    finally:
        cursor.close()
        conn.close()
