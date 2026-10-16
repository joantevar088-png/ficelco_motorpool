from django.urls import path
from . import views

urlpatterns = [
    # Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/', views.motorpool_dashboard, name='motorpool_dashboard'),
    path('department/dashboard/', views.department_dashboard, name='department_dashboard'),

    # Vehicle Requests
    path('request/create/', views.create_request, name='create_request'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
    path('request/<int:pk>/approve/', views.approve_request, name='approve_request'),
    path('request/<int:pk>/notify-pickup/', views.notify_pickup, name='notify_pickup'),
    path('requests/', views.request_list, name='request_list'),
    path('my-requests/', views.my_requests, name='my_requests'),

    # Signature Chain
    path('request/<int:pk>/sign/dispatcher/', views.sign_dispatcher, name='sign_dispatcher'),
    path('request/<int:pk>/sign/division-supervisor/', views.sign_division_supervisor, name='sign_division_supervisor'),
    path('request/<int:pk>/sign/department-manager/', views.sign_department_manager, name='sign_department_manager'),
    path('request/<int:pk>/sign/general-manager/', views.sign_general_manager, name='sign_general_manager'),
    path('request/<int:pk>/sign/guard/', views.sign_guard_on_duty, name='sign_guard_on_duty'),

    # Time Out / Time In
    path('request/<int:pk>/time-out/', views.time_out, name='time_out'),
    path('request/<int:pk>/time-in/', views.time_in, name='time_in'),

    # Barangay API
    path('api/barangays/<str:municipality>/', views.get_barangays, name='get_barangays'),

    # Live Tracking
    path('api/active-trips/', views.get_active_trips, name='get_active_trips'),
    path('api/trip-point/<int:trip_log_id>/add/', views.add_trip_point, name='add_trip_point'),
]