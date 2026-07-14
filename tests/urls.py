from django.urls import path
from . import views

app_name = 'tests'

urlpatterns = [
    # Packages (must match prior to general integer ID pattern to avoid conflict)
    path('packages', views.package_list_create, name='package_list_create'),
    path('packages/<int:id>', views.delete_package, name='delete_package'),

    # Test profiles & parameters
    path('', views.test_list_create, name='test_list_create'),
    path('<int:id>', views.test_detail_update_delete, name='test_detail'),
    path('<int:id>/parameters', views.update_test_parameters, name='update_test_parameters'),
]
