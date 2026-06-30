from django.urls import path
from . import views

urlpatterns = [
    # Dashboard HTML skeleton page
    path('', views.dashboard_view, name='dashboard'),
    
    # API endpoints
    path('api/analytics/dashboard-data/', views.DashboardDataAPIView.as_view(), name='api_dashboard_data'),
]
