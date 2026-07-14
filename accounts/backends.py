from django.contrib.auth.backends import BaseBackend
from werkzeug.security import check_password_hash
from .models import User

class WerkzeugAuthBackend(BaseBackend):
    """
    Custom Django authentication backend that verifies credentials using
    Werkzeug's password hashing scheme against the existing legacy Users table.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        
        user = User.objects.filter(email=username).first()
        if user and check_password_hash(user.password, password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
