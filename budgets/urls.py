from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'budgets', views.BudgetViewSet, basename='budget')

urlpatterns = [
    # HTML View
    path('budgets/', views.budgets_list_view, name='budgets_list'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
