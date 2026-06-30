from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reports', views.ReportViewSet, basename='report')

urlpatterns = [
    # HTML View
    path('reports/', views.reports_list_view, name='reports_list'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
