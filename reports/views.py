import json
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Sum
from accounts.models import User
from patients.models import Patient
from tests.models import TestParameter, Test
from .models import Report, ReportParameterResult

def is_auth(request):
    return request.user.is_authenticated

def get_role(request):
    return request.user.role if request.user.is_authenticated else None

@csrf_exempt
@require_http_methods(["GET"])
def billing_daily_collection(request):
    """
    Endpoint that fetches the last 100 billing records for Admin/Technician.
    Operators are forbidden.
    """
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if get_role(request) == 'Operator':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    role = get_role(request)
    branch_id = request.session.get('branch_id', 1)

    queryset = Report.objects.select_related('patient').exclude(status='Draft').order_by('-report_date', '-id')

    if role != 'Admin':
        queryset = queryset.filter(branch_id=branch_id)

    queryset = queryset[:100]

    data = []
    for r in queryset:
        data.append({
            'report_id': r.id,
            'report_date': r.report_date.strftime('%Y-%m-%d') if r.report_date else '',
            'patient_name': r.patient.name,
            'total_amount': float(r.total_amount),
            'discount': float(r.discount),
            'paid_amount': float(r.paid_amount),
            'balance_due': float(r.balance_due),
            'payment_status': r.payment_status
        })

    return JsonResponse(data, safe=False)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def report_list_create(request):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    role = get_role(request)
    branch_id = request.session.get('branch_id', 1)

    if request.method == "GET":
        queryset = Report.objects.select_related('patient', 'approved_by').all().order_by('-created_at')

        # Filter by branch if not Admin
        if role != 'Admin':
            queryset = queryset.filter(branch_id=branch_id)

        # Apply optional filters
        status = request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(patient__name__icontains=search)

        date_val = request.GET.get('date')
        if date_val:
            try:
                queryset = queryset.filter(created_at__date=date_val)
            except Exception:
                pass

        payment_status = request.GET.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        data = []
        for r in queryset:
            data.append({
                'id': r.id,
                'patient_id': r.patient.id,
                'patient_name': r.patient.name,
                'report_date': r.report_date.strftime('%Y-%m-%d') if r.report_date else '',
                'status': r.status,
                'total_amount': float(r.total_amount),
                'discount': float(r.discount),
                'paid_amount': float(r.paid_amount),
                'balance_due': float(r.balance_due),
                'payment_status': r.payment_status,
                'branch_id': r.branch_id,
                'approved_by': r.approved_by.id if r.approved_by else None,
                'approved_by_name': r.approved_by.name if r.approved_by else None,
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
            })
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        if role not in ['Admin', 'Operator']:
            return JsonResponse({'error': 'Forbidden'}, status=403)

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        patient_id = data.get('patient_id')
        parameters = data.get('parameters')  # list of {'parameter_id': x, 'result_value': y}

        if not patient_id or not parameters:
            return JsonResponse({'error': 'patient_id and parameters are required'}, status=400)

        total_amount = data.get('total_amount', 0.00)
        discount = data.get('discount', 0.00)
        paid_amount = data.get('paid_amount', 0.00)
        balance_due = data.get('balance_due', 0.00)
        payment_status = data.get('payment_status', 'Pending')
        status = data.get('status', 'Pending')
        if status not in ['Pending', 'Draft', 'Approved']:
            status = 'Pending'

        try:
            with transaction.atomic():
                report = Report.objects.create(
                    patient_id=patient_id,
                    status=status,
                    total_amount=total_amount,
                    discount=discount,
                    paid_amount=paid_amount,
                    balance_due=balance_due,
                    payment_status=payment_status,
                    branch_id=branch_id
                )

                role = get_role(request)
                if role != 'Admin':
                    from django.utils import timezone
                    report.report_date = timezone.now()
                    report.save()
                else:
                    report_date = data.get('report_date')
                    if report_date:
                        report.report_date = report_date
                        report.save()

                # Insert results
                for param in parameters:
                    ReportParameterResult.objects.create(
                        report=report,
                        parameter_id=param['parameter_id'],
                        result_value=param['result_value']
                    )

            return JsonResponse({'message': 'Report created successfully', 'id': report.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def report_detail_update_delete(request, id):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    role = get_role(request)
    branch_id = request.session.get('branch_id', 1)

    report = Report.objects.filter(id=id).select_related('patient', 'approved_by').first()
    if not report:
        return JsonResponse({'error': 'Report not found'}, status=404)

    # Branch authorization filter
    if role != 'Admin' and report.branch_id != branch_id:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == "GET":
        # Get results joining test and parameter
        results = ReportParameterResult.objects.filter(report_id=id).select_related('parameter', 'parameter__test').order_by('parameter__test_id', 'parameter__display_order')
        
        details = []
        for r in results:
            details.append({
                'id': r.id,
                'parameter_id': r.parameter.id,
                'result_value': r.result_value,
                'parameter_name': r.parameter.parameter_name,
                'unit': r.parameter.unit,
                'normal_range': r.parameter.normal_range,
                'parameter_type': r.parameter.parameter_type,
                'test_id': r.parameter.test.id,
                'test_name': r.parameter.test.test_name,
                'price': float(r.parameter.test.price)
            })

        return JsonResponse({
            'id': report.id,
            'patient_id': report.patient.id,
            'patient_name': report.patient.name,
            'age': report.patient.age,
            'gender': report.patient.gender,
            'date': report.patient.date.strftime('%Y-%m-%d') if report.patient.date else '',
            'referred_doctor': report.patient.referred_doctor,
            'report_date': report.report_date.strftime('%Y-%m-%d') if report.report_date else '',
            'status': report.status,
            'total_amount': float(report.total_amount),
            'discount': float(report.discount),
            'paid_amount': float(report.paid_amount),
            'balance_due': float(report.balance_due),
            'payment_status': report.payment_status,
            'branch_id': report.branch_id,
            'approved_by': report.approved_by.id if report.approved_by else None,
            'approved_by_name': report.approved_by.name if report.approved_by else None,
            'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S') if report.created_at else '',
            'details': details
        })

    elif request.method == "PUT":
        if role not in ['Admin', 'Technician']:
            return JsonResponse({'error': 'Forbidden'}, status=403)

        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        parameters = data.get('parameters')
        if not parameters:
            return JsonResponse({'error': 'parameters are required'}, status=400)

        try:
            with transaction.atomic():
                report.total_amount = data.get('total_amount', report.total_amount)
                report.discount = data.get('discount', report.discount)
                report.paid_amount = data.get('paid_amount', report.paid_amount)
                report.balance_due = data.get('balance_due', report.balance_due)
                report.payment_status = data.get('payment_status', report.payment_status)
                
                status = data.get('status', 'Pending')
                if status not in ['Pending', 'Draft', 'Approved']:
                    status = 'Pending'
                report.status = status

                report_date = data.get('report_date')
                if report_date:
                    if role != 'Admin':
                        existing_date_str = report.report_date.strftime('%Y-%m-%d') if report.report_date else ''
                        input_date_str = report_date.split('T')[0].split(' ')[0]
                        if input_date_str != existing_date_str:
                            return JsonResponse({'error': 'Only Administrators can edit the report date'}, status=403)
                    else:
                        report.report_date = report_date
                
                # Resets approval when edited
                report.approved_by = None
                report.save()

                # Clear and insert new parameter values
                ReportParameterResult.objects.filter(report_id=id).delete()
                for param in parameters:
                    ReportParameterResult.objects.create(
                        report=report,
                        parameter_id=param['parameter_id'],
                        result_value=param['result_value']
                    )

            return JsonResponse({'message': 'Report updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == "DELETE":
        if role != 'Admin':
            return JsonResponse({'error': 'Forbidden'}, status=403)

        report.delete()
        return JsonResponse({'message': 'Report deleted successfully'})

@csrf_exempt
@require_http_methods(["PUT"])
def approve_report(request, id):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if get_role(request) not in ['Admin', 'Technician']:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    report = Report.objects.filter(id=id).first()
    if not report:
        return JsonResponse({'error': 'Report not found'}, status=404)

    report.status = 'Approved'
    report.approved_by = request.user
    report.save()

    return JsonResponse({'message': 'Report approved successfully'})

@require_http_methods(["GET"])
def daily_collection(request):
    if not is_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    role = get_role(request)
    branch_id = request.session.get('branch_id', 1)
    target_date = request.GET.get('date')

    if target_date:
        try:
            query_date = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
        except Exception:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    else:
        query_date = datetime.date.today()

    reports_for_date = Report.objects.filter(created_at__date=query_date).exclude(status='Draft')

    if role != 'Admin':
        reports_for_date = reports_for_date.filter(branch_id=branch_id)

    # Calculate Aggregations
    aggregates = reports_for_date.aggregate(
        total_revenue=Sum('total_amount'),
        total_discount=Sum('discount'),
        total_collected=Sum('paid_amount'),
        total_pending=Sum('balance_due')
    )

    summary = {
        'total_revenue': float(aggregates['total_revenue'] or 0.00),
        'total_discount': float(aggregates['total_discount'] or 0.00),
        'total_collected': float(aggregates['total_collected'] or 0.00),
        'total_pending': float(aggregates['total_pending'] or 0.00)
    }

    # Get individual reports list
    reports_list = []
    for r in reports_for_date.select_related('patient').order_by('-created_at'):
        reports_list.append({
            'id': r.id,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'patient_name': r.patient.name,
            'total_amount': float(r.total_amount),
            'discount': float(r.discount),
            'paid_amount': float(r.paid_amount),
            'balance_due': float(r.balance_due),
            'payment_status': r.payment_status
        })

    return JsonResponse({
        'summary': summary,
        'reports': reports_list
    })
