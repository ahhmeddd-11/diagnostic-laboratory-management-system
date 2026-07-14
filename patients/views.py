import json
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Patient

def is_auth(request):
    return request.user.is_authenticated

def get_role(request):
    return request.user.role if request.user.is_authenticated else None

@csrf_exempt
@require_http_methods(["GET", "POST"])
def patient_list_create(request):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == "GET":
        patients = Patient.objects.all().order_by('-id')
        data = []
        for p in patients:
            data.append({
                'id': p.id,
                'name': p.name,
                'age': p.age,
                'gender': p.gender,
                'date': p.date.strftime('%Y-%m-%d') if p.date else '',
                'referred_doctor': p.referred_doctor,
                'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else ''
            })
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        if get_role(request) not in ['Admin', 'Operator']:
            return JsonResponse({'error': 'Forbidden'}, status=403)

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        required = ['name', 'age', 'gender', 'date']
        if not all(k in data for k in required):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        role = get_role(request)
        if role != 'Admin':
            data['date'] = datetime.date.today().strftime('%Y-%m-%d')

        try:
            patient = Patient.objects.create(
                name=data['name'],
                age=data['age'],
                gender=data['gender'],
                date=data['date'],
                referred_doctor=data.get('referred_doctor')
            )
            return JsonResponse({'message': 'Patient added successfully', 'id': patient.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def patient_detail(request, id):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    patient = Patient.objects.filter(id=id).first()
    if not patient:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    if request.method == "GET":
        return JsonResponse({
            'id': patient.id,
            'name': patient.name,
            'age': patient.age,
            'gender': patient.gender,
            'date': patient.date.strftime('%Y-%m-%d') if patient.date else '',
            'referred_doctor': patient.referred_doctor,
            'created_at': patient.created_at.strftime('%Y-%m-%d %H:%M:%S') if patient.created_at else ''
        })

    elif request.method == "PUT":
        if get_role(request) not in ['Admin', 'Operator']:
            return JsonResponse({'error': 'Forbidden'}, status=403)

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        role = get_role(request)
        if role != 'Admin' and 'date' in data:
            existing_date_str = patient.date.strftime('%Y-%m-%d') if patient.date else ''
            if data['date'] != existing_date_str:
                return JsonResponse({'error': 'Only Administrators can edit the registration date'}, status=403)

        try:
            patient.name = data.get('name', patient.name)
            patient.age = data.get('age', patient.age)
            patient.gender = data.get('gender', patient.gender)
            patient.date = data.get('date', patient.date)
            patient.referred_doctor = data.get('referred_doctor', patient.referred_doctor)
            patient.save()
            return JsonResponse({'message': 'Patient updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == "DELETE":
        if get_role(request) != 'Admin':
            return JsonResponse({'error': 'Forbidden'}, status=403)

        patient.delete()
        return JsonResponse({'message': 'Patient deleted successfully'})

