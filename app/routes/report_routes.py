from flask import Blueprint, request, jsonify, session
from app.models.db import get_db_connection

report_bp = Blueprint('report', __name__)

def is_auth():
    return 'user_id' in session

@report_bp.route('/billing/daily-collection', methods=['GET'])
def get_daily_collection():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') == 'Operator': return jsonify({'error': 'Forbidden'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                r.id as report_id,
                r.report_date,
                p.name as patient_name,
                r.total_amount,
                r.discount,
                r.paid_amount,
                r.balance_due,
                r.payment_status
            FROM Reports r
            JOIN Patients p ON r.patient_id = p.id
            WHERE r.status != 'Draft' {branch_filter}
            ORDER BY r.report_date DESC, r.id DESC
            LIMIT 100
        """
        if session.get('role') != 'Admin':
            query = query.replace('{branch_filter}', 'AND r.branch_id = %s')
            cursor.execute(query, (session.get('branch_id', 1),))
        else:
            query = query.replace('{branch_filter}', '')
            cursor.execute(query)
        billing_records = cursor.fetchall()
        for record in billing_records:
            record['report_date'] = str(record['report_date'])
            for field in ['total_amount', 'discount', 'paid_amount', 'balance_due']:
                record[field] = float(record[field] or 0)
        return jsonify(billing_records)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@report_bp.route('/', methods=['GET'])
def get_reports():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT r.*, p.name as patient_name, u.name as approved_by_name 
            FROM Reports r
            JOIN Patients p ON r.patient_id = p.id
            LEFT JOIN Users u ON r.approved_by = u.id
            {branch_filter}
            ORDER BY r.created_at DESC
        """
        if session.get('role') != 'Admin':
            query = query.replace('{branch_filter}', 'WHERE r.branch_id = %s')
            cursor.execute(query, (session.get('branch_id', 1),))
        else:
            query = query.replace('{branch_filter}', '')
            cursor.execute(query)
        reports = cursor.fetchall()
        for r in reports:
            r['created_at'] = str(r['created_at'])
            if r.get('report_date'):
                r['report_date'] = str(r['report_date'])
            for field in ['total_amount', 'discount', 'paid_amount', 'balance_due']:
                if r.get(field) is not None:
                    r[field] = float(r[field])
        return jsonify(reports)
    finally:
        cursor.close()
        conn.close()

@report_bp.route('/<int:id>', methods=['GET'])
def get_report_details(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get Report Info
        query = """
            SELECT r.*, p.name as patient_name, p.age, p.gender, p.date, p.referred_doctor, u.name as approved_by_name 
            FROM Reports r
            JOIN Patients p ON r.patient_id = p.id
            LEFT JOIN Users u ON r.approved_by = u.id
            WHERE r.id = %s {branch_filter}
        """
        if session.get('role') != 'Admin':
            query = query.replace('{branch_filter}', 'AND r.branch_id = %s')
            cursor.execute(query, (id, session.get('branch_id', 1)))
        else:
            query = query.replace('{branch_filter}', '')
            cursor.execute(query, (id,))
        report = cursor.fetchone()
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
            
        report['created_at'] = str(report['created_at'])
        if report.get('report_date'):
            report['report_date'] = str(report['report_date'])
        report['date'] = str(report['date'])
        for field in ['total_amount', 'discount', 'paid_amount', 'balance_due']:
            if report.get(field) is not None:
                report[field] = float(report[field])
            
        # Get Test Details with dynamic parameters
        cursor.execute("""
            SELECT rpr.id, rpr.result_value, tp.parameter_name, tp.unit, tp.normal_range, tp.parameter_type, t.test_name, t.price, tp.id as parameter_id, t.id as test_id
            FROM Report_Parameter_Results rpr
            JOIN Test_Parameters tp ON rpr.parameter_id = tp.id
            JOIN Tests t ON tp.test_id = t.id
            WHERE rpr.report_id = %s
            ORDER BY t.id, tp.display_order
        """, (id,))
        details = cursor.fetchall()
        
        for d in details:
            d['price'] = float(d['price'])
            
        report['details'] = details
        return jsonify(report)
    finally:
        cursor.close()
        conn.close()

@report_bp.route('/', methods=['POST'])
def create_report():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') not in ['Admin', 'Operator']:
        return jsonify({'error': 'Forbidden'}), 403
        
    data = request.json
    patient_id = data.get('patient_id')
    report_date = data.get('report_date')
    parameters = data.get('parameters') # List of dicts: [{'parameter_id': 1, 'result_value': '12.5'}, ...]
    
    total_amount = data.get('total_amount', 0)
    discount = data.get('discount', 0)
    paid_amount = data.get('paid_amount', 0)
    balance_due = data.get('balance_due', 0)
    payment_status = data.get('payment_status', 'Pending')
    status = data.get('status', 'Pending')
    if status not in ['Pending', 'Draft', 'Approved']:
        status = 'Pending'
    branch_id = session.get('branch_id', 1)
    
    if not patient_id or not parameters:
        return jsonify({'error': 'patient_id and parameters are required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if report_date:
            cursor.execute("""
                INSERT INTO Reports (patient_id, report_date, status, total_amount, discount, paid_amount, balance_due, payment_status, branch_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (patient_id, report_date, status, total_amount, discount, paid_amount, balance_due, payment_status, branch_id))
        else:
            cursor.execute("""
                INSERT INTO Reports (patient_id, status, total_amount, discount, paid_amount, balance_due, payment_status, branch_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (patient_id, status, total_amount, discount, paid_amount, balance_due, payment_status, branch_id))
        report_id = cursor.lastrowid
        
        for param in parameters:
            cursor.execute("""
                INSERT INTO Report_Parameter_Results (report_id, parameter_id, result_value) 
                VALUES (%s, %s, %s)
            """, (report_id, param['parameter_id'], param['result_value']))
            
        conn.commit()
        return jsonify({'message': 'Report created successfully', 'id': report_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@report_bp.route('/<int:id>/approve', methods=['PUT'])
def approve_report(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') not in ['Admin', 'Technician']:
        return jsonify({'error': 'Forbidden'}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Reports SET status = 'Approved', approved_by = %s
            WHERE id = %s
        """, (session['user_id'], id))
        conn.commit()
        return jsonify({'message': 'Report approved successfully'})
    finally:
        cursor.close()
        conn.close()

@report_bp.route('/<int:id>', methods=['PUT'])
def update_report(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') not in ['Admin', 'Technician']:
        return jsonify({'error': 'Forbidden'}), 403
        
    data = request.json
    report_date = data.get('report_date')
    parameters = data.get('parameters')
    
    total_amount = data.get('total_amount', 0)
    discount = data.get('discount', 0)
    paid_amount = data.get('paid_amount', 0)
    balance_due = data.get('balance_due', 0)
    payment_status = data.get('payment_status', 'Pending')
    status = data.get('status', 'Pending')
    if status not in ['Pending', 'Draft', 'Approved']:
        status = 'Pending'
    
    if not parameters:
        return jsonify({'error': 'parameters are required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if report_date:
            cursor.execute("""
                UPDATE Reports SET report_date = %s, total_amount = %s, discount = %s, paid_amount = %s, balance_due = %s, payment_status = %s, status = %s
                WHERE id = %s
            """, (report_date, total_amount, discount, paid_amount, balance_due, payment_status, status, id))
        else:
            cursor.execute("""
                UPDATE Reports SET total_amount = %s, discount = %s, paid_amount = %s, balance_due = %s, payment_status = %s, status = %s
                WHERE id = %s
            """, (total_amount, discount, paid_amount, balance_due, payment_status, status, id))
            
        cursor.execute("DELETE FROM Report_Parameter_Results WHERE report_id = %s", (id,))
        for param in parameters:
            cursor.execute("""
                INSERT INTO Report_Parameter_Results (report_id, parameter_id, result_value) 
                VALUES (%s, %s, %s)
            """, (id, param['parameter_id'], param['result_value']))
            
        # Reset status if it was not passed as Draft
        if status != 'Draft':
            cursor.execute("UPDATE Reports SET status = 'Pending', approved_by = NULL WHERE id = %s", (id,))
        else:
            cursor.execute("UPDATE Reports SET status = 'Draft', approved_by = NULL WHERE id = %s", (id,))
        
        conn.commit()
        return jsonify({'message': 'Report updated successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@report_bp.route('/<int:id>', methods=['DELETE'])
def delete_report(id):
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    if session.get('role') != 'Admin':
        return jsonify({'error': 'Forbidden'}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Reports WHERE id = %s", (id,))
        conn.commit()
        return jsonify({'message': 'Report deleted successfully'})
    finally:
        cursor.close()
        conn.close()

@report_bp.route('/daily-collection', methods=['GET'])
def daily_collection():
    if not is_auth(): return jsonify({'error': 'Unauthorized'}), 401
    
    # Optional: filter by date or get all for the current day
    target_date = request.args.get('date')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        branch_id = session.get('branch_id', 1)
        is_admin = session.get('role') == 'Admin'
        
        if target_date:
            query = """
                SELECT 
                    SUM(total_amount) as total_revenue,
                    SUM(discount) as total_discount,
                    SUM(paid_amount) as total_collected,
                    SUM(balance_due) as total_pending
                FROM Reports
                WHERE DATE(created_at) = %s AND status != 'Draft' {branch_filter}
            """
            if not is_admin:
                query = query.replace('{branch_filter}', 'AND branch_id = %s')
                cursor.execute(query, (target_date, branch_id))
            else:
                query = query.replace('{branch_filter}', '')
                cursor.execute(query, (target_date,))
        else:
            # If no date provided, get today's collection
            query = """
                SELECT 
                    SUM(total_amount) as total_revenue,
                    SUM(discount) as total_discount,
                    SUM(paid_amount) as total_collected,
                    SUM(balance_due) as total_pending
                FROM Reports
                WHERE DATE(created_at) = CURDATE() AND status != 'Draft' {branch_filter}
            """
            if not is_admin:
                query = query.replace('{branch_filter}', 'AND branch_id = %s')
                cursor.execute(query, (branch_id,))
            else:
                query = query.replace('{branch_filter}', '')
                cursor.execute(query)
            
        summary = cursor.fetchone()
        
        # Convert Decimals to float
        if summary:
            for k, v in summary.items():
                summary[k] = float(v) if v is not None else 0.0
        else:
            summary = {
                'total_revenue': 0.0,
                'total_discount': 0.0,
                'total_collected': 0.0,
                'total_pending': 0.0
            }
            
        # Get individual reports for that date
        if target_date:
            query = """
                SELECT r.id, r.created_at, p.name as patient_name, r.total_amount, r.discount, r.paid_amount, r.balance_due, r.payment_status
                FROM Reports r
                JOIN Patients p ON r.patient_id = p.id
                WHERE DATE(r.created_at) = %s AND r.status != 'Draft' {branch_filter}
                ORDER BY r.created_at DESC
            """
            if not is_admin:
                query = query.replace('{branch_filter}', 'AND r.branch_id = %s')
                cursor.execute(query, (target_date, branch_id))
            else:
                query = query.replace('{branch_filter}', '')
                cursor.execute(query, (target_date,))
        else:
            query = """
                SELECT r.id, r.created_at, p.name as patient_name, r.total_amount, r.discount, r.paid_amount, r.balance_due, r.payment_status
                FROM Reports r
                JOIN Patients p ON r.patient_id = p.id
                WHERE DATE(r.created_at) = CURDATE() AND r.status != 'Draft' {branch_filter}
                ORDER BY r.created_at DESC
            """
            if not is_admin:
                query = query.replace('{branch_filter}', 'AND r.branch_id = %s')
                cursor.execute(query, (branch_id,))
            else:
                query = query.replace('{branch_filter}', '')
                cursor.execute(query)
            
        reports = cursor.fetchall()
        for r in reports:
            r['created_at'] = str(r['created_at'])
            for field in ['total_amount', 'discount', 'paid_amount', 'balance_due']:
                if r.get(field) is not None:
                    r[field] = float(r[field])
                    
        return jsonify({
            'summary': summary,
            'reports': reports
        })
    finally:
        cursor.close()
        conn.close()
