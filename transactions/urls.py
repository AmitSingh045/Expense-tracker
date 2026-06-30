from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'currencies', views.CurrencyViewSet, basename='currency')
router.register(r'payment-methods', views.PaymentMethodViewSet, basename='paymentmethod')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'bills', views.BillViewSet, basename='bill')

urlpatterns = [
    # HTML Pages
    path('transactions/', views.transactions_list_view, name='transactions_list'),
    path('bills/', views.bills_list_view, name='bills_list'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
