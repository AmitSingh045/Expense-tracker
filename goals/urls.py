from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'goals', views.GoalViewSet, basename='goal')

urlpatterns = [
    # HTML View
    path('goals/', views.goals_list_view, name='goals_list'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
