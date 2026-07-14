from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, name, role, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            name=name,
            role=role
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, role, password=None):
        return self.create_user(email, name, role, password)

class User(AbstractBaseUser):
    # Explicitly match the 32-bit INT AUTO_INCREMENT of the existing MySQL table
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    role = models.CharField(max_length=50)  # Admin, Technician, Operator
    profile_photo = models.CharField(max_length=255, null=True, blank=True)
    branch_id = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    # Disable last_login database field to maintain compatibility with the existing Users schema
    last_login = None

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'role']

    class Meta:
        db_table = 'Users'
