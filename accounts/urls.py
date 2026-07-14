from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Session authentication endpoints (api/auth/...)
    path('auth/login', views.login_view, name='login'),
    path('auth/logout', views.logout_view, name='logout'),
    path('auth/me', views.get_me, name='me'),
    path('auth/change-password', views.change_password, name='change_password'),
    path('auth/profile-photo', views.upload_profile_photo, name='upload_profile_photo'),

    # User administration endpoints (api/users/...)
    path('users/', views.user_list_create, name='user_list_create'),
    path('users/<int:id>', views.user_detail_update_delete, name='user_detail'),
]
