from django.urls import path
from . import views

urlpatterns = [
    path('live-map/', views.live_map, name='live_map'),
    path('trip/<int:pk>/history/', views.trip_history, name='trip_history'),
]