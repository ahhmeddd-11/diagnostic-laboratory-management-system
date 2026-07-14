from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Daily Collection ledger and billing records list
    path('daily-collection', views.daily_collection, name='daily_collection'),
    path('billing/daily-collection', views.billing_daily_collection, name='billing_daily_collection'),

    # Reports general endpoints
    path('', views.report_list_create, name='report_list_create'),
    path('<int:id>', views.report_detail_update_delete, name='report_detail'),
    path('<int:id>/approve', views.approve_report, name='approve_report'),
]
