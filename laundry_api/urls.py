from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomerViewSet, StaffViewSet, GarmentTypeViewSet,
    ServiceTypeViewSet, OrderViewSet, InvoiceViewSet,
    PaymentViewSet, FeedbackViewSet, ReceiptViewSet,
    RegisterView, LoginView, LogoutView, UserProfileView,
    check_username, check_email, update_order_status, update_payment_status, AssignOrderStaffView
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'staff', StaffViewSet)
router.register(r'garment-types', GarmentTypeViewSet)
router.register(r'service-types', ServiceTypeViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'receipts', ReceiptViewSet)
router.register(r'feedbacks', FeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('orders/<int:pk>/status/', update_order_status, name='order-status-update'),
    path('payments/<int:pk>/status/', update_payment_status, name='payment-status-update'),
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/check-username/', check_username, name='check_username'),
    path('auth/check-email/', check_email, name='check_email'),
    path('orders/<int:order_id>/assign-staff/', AssignOrderStaffView.as_view(), name='assign-order-staff'),
]