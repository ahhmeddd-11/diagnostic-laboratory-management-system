from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from app_paths import STATIC_DIR

urlpatterns = [
    # Frontend Page Layouts served via standard TemplateViews
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('dashboard', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('print', TemplateView.as_view(template_name='print_report.html'), name='print'),
    path('setup', TemplateView.as_view(template_name='setup.html'), name='setup'),

    # Modular API Routing namespaces
    path('api/patients/', include('patients.urls')),
    path('api/tests/', include('tests.urls')),
    path('api/reports/', include('reports.urls')),
    
    # Unified API routing for authentication, users, logs, and setup
    path('api/', include('accounts.urls')),
    path('api/', include('core.urls')),
]

# Serve static files and media assets locally for user profiles in development/local execution
if settings.DEBUG:
    urlpatterns += static(
    settings.STATIC_URL,
    document_root=STATIC_DIR
)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
