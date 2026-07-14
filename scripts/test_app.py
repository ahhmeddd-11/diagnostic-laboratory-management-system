import urllib.request
import urllib.error
import json
import time

BASE_URL = 'http://localhost:5000/api'
cookie = None

def make_request(endpoint, method='GET', data=None):
    global cookie
    url = BASE_URL + endpoint
    headers = {'Content-Type': 'application/json'}
    if cookie:
        headers['Cookie'] = cookie
        
    req = urllib.request.Request(url, method=method, headers=headers)
    if data:
        req.data = json.dumps(data).encode('utf-8')
        
    try:
        res = urllib.request.urlopen(req)
        if not cookie and res.headers.get('Set-Cookie'):
            cookie = res.headers.get('Set-Cookie')
            
        return res.getcode(), json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))
    except Exception as e:
        return 500, {'error': str(e)}

def test_app():
    print("Testing Auth /login...")
    status, res = make_request('/auth/login', 'POST', {'email': 'admin@lab.com', 'password': 'admin123'})
    print(f"Login: {status} - {res}")
    
    print("\nTesting Patients /patients...")
    status, res = make_request('/patients/')
    print(f"Get Patients: {status} - {len(res) if isinstance(res, list) else res} patients found")
    
    print("\nAdding a patient...")
    status, res = make_request('/patients/', 'POST', {
        'name': 'Test Patient',
        'age': 30,
        'gender': 'Male',
        'date': '2026-05-07',
        'referred_doctor': 'Dr. Smith'
    })
    print(f"Add Patient: {status} - {res}")
    patient_id = res.get('id') if isinstance(res, dict) else None
    
    print("\nTesting Tests /tests...")
    status, res = make_request('/tests/')
    print(f"Get Tests: {status} - {len(res) if isinstance(res, list) else res} tests found")
    
    print("\nAdding a report...")
    if patient_id:
        status, res = make_request('/reports/', 'POST', {
            'patient_id': patient_id,
            'report_date': '2026-05-07',
            'parameters': [{'parameter_id': 1, 'result_value': '12.5'}]
        })
        print(f"Add Report: {status} - {res}")
    
    print("\nTesting Users /users...")
    status, res = make_request('/users/')
    print(f"Get Users: {status} - {len(res) if isinstance(res, list) else res} users found")
    
    print("\nAdding a user...")
    status, res = make_request('/users/', 'POST', {
        'name': 'Test Tech',
        'email': 'tech@lab.com',
        'password': 'password123',
        'role': 'Technician'
    })
    print(f"Add User: {status} - {res}")
    
    print("\nTesting Logs /logs...")
    status, res = make_request('/logs/')
    print(f"Get Logs: {status} - {len(res) if isinstance(res, list) else res} logs found")

if __name__ == '__main__':
    test_app()
