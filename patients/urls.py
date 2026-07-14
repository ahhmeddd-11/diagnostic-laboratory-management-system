from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.patient_list_create, name='patient_list_create'),
    path('<int:id>', views.patient_detail, name='patient_detail'),
]
