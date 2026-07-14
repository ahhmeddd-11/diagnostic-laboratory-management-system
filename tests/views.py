import json
from collections import defaultdict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Test, TestParameter, TestPackage

def is_auth(request):
    return request.user.is_authenticated

def get_role(request):
    return request.user.role if request.user.is_authenticated else None

@csrf_exempt
@require_http_methods(["GET", "POST"])
def test_list_create(request):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == "GET":
        tests = Test.objects.all().order_by('test_name')
        
        # Optimize query by fetching all parameters and grouping in-memory (prevents N+1)
        params = TestParameter.objects.all().order_by('test_id', 'display_order')
        params_by_test = defaultdict(list)
        for p in params:
            params_by_test[p.test_id].append({
                'id': p.id,
                'test_id': p.test_id,
                'parameter_name': p.parameter_name,
                'unit': p.unit,
                'normal_range': p.normal_range,
                'display_order': p.display_order,
                'formula': p.formula,
                'parameter_type': p.parameter_type
            })

        data = []
        for t in tests:
            data.append({
                'id': t.id,
                'test_name': t.test_name,
                'normal_range': t.normal_range,
                'price': float(t.price),
                'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S') if t.created_at else '',
                'parameters': params_by_test.get(t.id, [])
            })
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        if get_role(request) not in ['Admin', 'Technician']:
            return JsonResponse({'error': 'Forbidden'}, status=403)

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        required = ['test_name', 'normal_range', 'price']
        if not all(k in data for k in required):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        try:
            test = Test.objects.create(
                test_name=data['test_name'],
                normal_range=data['normal_range'],
                price=data['price']
            )
            return JsonResponse({'message': 'Test added successfully', 'id': test.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def test_detail_update_delete(request, id):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    test = Test.objects.filter(id=id).first()
    if not test:
        return JsonResponse({'error': 'Test not found'}, status=404)

    if request.method == "PUT":
        if get_role(request) not in ['Admin', 'Technician']:
            return JsonResponse({'error': 'Forbidden'}, status=403)

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        try:
            test.test_name = data.get('test_name', test.test_name)
            test.normal_range = data.get('normal_range', test.normal_range)
            test.price = data.get('price', test.price)
            test.save()
            return JsonResponse({'message': 'Test updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == "DELETE":
        if get_role(request) != 'Admin':
            return JsonResponse({'error': 'Forbidden'}, status=403)

        test.delete()
        return JsonResponse({'message': 'Test deleted successfully'})

@csrf_exempt
@require_http_methods(["PUT"])
def update_test_parameters(request, id):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if get_role(request) not in ['Admin', 'Technician']:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        data = json.loads(request.body)  # Expected: List of parameter dicts
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        # Clear existing parameters first (matching Flask logic)
        TestParameter.objects.filter(test_id=id).delete()

        # Insert new parameters
        for p in data:
            TestParameter.objects.create(
                test_id=id,
                parameter_name=p['parameter_name'],
                unit=p.get('unit', ''),
                normal_range=p.get('normal_range', ''),
                display_order=p.get('display_order', 0),
                formula=p.get('formula'),
                parameter_type=p.get('parameter_type', 'text')
            )

        return JsonResponse({'message': 'Parameters updated successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def package_list_create(request):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == "GET":
        packages = TestPackage.objects.all().order_by('package_name')
        data = []
        for p in packages:
            tests = p.tests.all()
            tests_list = []
            for t in tests:
                tests_list.append({
                    'id': t.id,
                    'test_name': t.test_name,
                    'normal_range': t.normal_range,
                    'price': float(t.price)
                })

            data.append({
                'id': p.id,
                'package_name': p.package_name,
                'price': float(p.price),
                'description': p.description,
                'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else '',
                'tests': tests_list
            })
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        if get_role(request) != 'Admin':
            return JsonResponse({'error': 'Forbidden'}, status=403)

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        package_name = data.get('package_name')
        price = data.get('price')
        description = data.get('description', '')
        test_ids = data.get('test_ids', [])

        if not package_name or price is None:
            return JsonResponse({'error': 'package_name and price are required'}, status=400)

        try:
            package = TestPackage.objects.create(
                package_name=package_name,
                price=price,
                description=description
            )
            # Add relationships inside Test_Package_Tests
            package.tests.add(*test_ids)
            return JsonResponse({'message': 'Package created successfully', 'id': package.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_package(request, id):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if get_role(request) != 'Admin':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    package = TestPackage.objects.filter(id=id).first()
    if not package:
        return JsonResponse({'error': 'Package not found'}, status=404)

    package.delete()
    return JsonResponse({'message': 'Package deleted successfully'})
