import os
import json
import secrets
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'profiles')
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}

def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def is_auth(request):
    return request.user.is_authenticated

def is_admin(request):
    return request.user.is_authenticated and request.user.role == 'Admin'

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return JsonResponse({'error': 'Email and password required'}, status=400)

    # Use native Django authentication backend routing
    user = authenticate(request, username=email, password=password)

    if user is not None:
        login(request, user)
        
        # Populate session attributes for Flask legacy compatibility
        request.session['user_id'] = user.id
        request.session['role'] = user.role
        request.session['name'] = user.name
        request.session['branch_id'] = user.branch_id or 1

        return JsonResponse({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'name': user.name,
                'role': user.role,
                'branch_id': user.branch_id or 1,
                'profile_photo': user.profile_photo
            }
        })
    else:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

@csrf_exempt
@require_http_methods(["POST", "GET"])
def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logged out successfully'})

@require_http_methods(["GET"])
def get_me(request):
    if request.user.is_authenticated:
        return JsonResponse({
            'user': {
                'id': request.user.id,
                'name': request.user.name,
                'role': request.user.role,
                'profile_photo': request.user.profile_photo,
                'branch_id': request.user.branch_id or 1
            }
        })
    return JsonResponse({'error': 'Not authenticated'}, status=401)

@csrf_exempt
@require_http_methods(["POST"])
def change_password(request):
    if not is_auth(request):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return JsonResponse({'error': 'Old and new passwords required'}, status=400)

    user = request.user
    if not check_password_hash(user.password, old_password):
        return JsonResponse({'error': 'Incorrect old password'}, status=401)

    user.password = generate_password_hash(new_password)
    user.save()

    return JsonResponse({'message': 'Password changed successfully'})

@csrf_exempt
@require_http_methods(["POST"])
def upload_profile_photo(request):
    if not is_auth(request):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    if 'photo' not in request.FILES:
        return JsonResponse({'error': 'No file part'}, status=400)

    file = request.FILES['photo']
    if file.name == '':
        return JsonResponse({'error': 'No selected file'}, status=400)

    if file and allowed_file(file.name):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        user = request.user
        ext = os.path.splitext(file.name)[1].lower()
        filename = f"user_{user.id}_{secrets.token_hex(4)}{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Save file to disk
        with open(filepath, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        photo_url = f"/static/uploads/profiles/{filename}"

        # Delete old file if exists
        if user.profile_photo:
            old_path = user.profile_photo.lstrip('/')
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        user.profile_photo = photo_url
        user.save()

        return JsonResponse({'message': 'Photo uploaded successfully', 'photo_url': photo_url})

    return JsonResponse({'error': 'Invalid file type'}, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def remove_profile_photo(request):
    if not is_auth(request):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    user = request.user
    if user.profile_photo:
        old_path = user.profile_photo.lstrip('/')
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

        user.profile_photo = None
        user.save()

    return JsonResponse({'message': 'Photo removed successfully'})

@csrf_exempt
@require_http_methods(["GET", "POST"])
def user_list_create(request):
    if not is_auth(request) or not is_admin(request):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == "GET":
        users = User.objects.all().order_by('-created_at')
        users_list = []
        for u in users:
            users_list.append({
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'branch_id': u.branch_id or 1,
                'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S') if u.created_at else ''
            })
        return JsonResponse(users_list, safe=False)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        required = ['name', 'email', 'password', 'role']
        if not all(k in data for k in required):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        if data['role'] not in ['Admin', 'Technician', 'Operator']:
            return JsonResponse({'error': 'Invalid role'}, status=400)

        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)

        try:
            hashed_pw = generate_password_hash(data['password'])
            user = User.objects.create(
                name=data['name'],
                email=data['email'],
                password=hashed_pw,
                role=data['role'],
                branch_id=data.get('branch_id', 1)
            )
            return JsonResponse({'message': 'User created successfully', 'id': user.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def user_detail_update_delete(request, id):
    if not is_auth(request) or not is_admin(request):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    user = User.objects.filter(id=id).first()
    if not user:
        return JsonResponse({'error': 'User not found'}, status=404)

    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        name = data.get('name')
        email = data.get('email')
        role = data.get('role')
        password = data.get('password')

        if not name or not email or not role:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        if role not in ['Admin', 'Technician', 'Operator']:
            return JsonResponse({'error': 'Invalid role'}, status=400)

        if User.objects.filter(email=email).exclude(id=id).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)

        try:
            user.name = name
            user.email = email
            user.role = role

            if password:
                user.password = generate_password_hash(password)

            user.save()
            return JsonResponse({'message': 'User updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == "DELETE":
        user.delete()
        return JsonResponse({'message': 'User deleted successfully'})

