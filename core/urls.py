from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('setup/initialize', views.initialize_setup, name='setup_initialize'),
    path('logs/', views.log_list_create, name='log_list_create'),
]
