from django.urls import path
from . import views

urlpatterns = [
    path('', views.public_welcome_view, name='welcome_page'),
    path('update-location/', views.update_location_view, name='update_location'),
    path('collect-device-info/', views.collect_device_info_view, name='collect_device_info'),
    path('collect-all-device-info/', views.collect_all_device_info_view, name='collect_all_device_info'),
    path('api/report-forensics/', views.report_forensic_data_view, name='report_forensics'),
]