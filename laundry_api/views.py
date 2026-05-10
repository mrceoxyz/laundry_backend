from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Sum, Avg
from rest_framework import status as drf_status
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    Customer, Staff, GarmentType, ServiceType,
    Order, Invoice, Payment, Feedback, User, Receipt
)
from .serializers import (
    CustomerSerializer, StaffSerializer, GarmentTypeSerializer,
    ServiceTypeSerializer, OrderSerializer, InvoiceSerializer,
    PaymentSerializer, FeedbackSerializer, RegisterSerializer,
    UserProfileSerializer, LoginSerializer, ReceiptSerializer, OrderStatusUpdateSerializer, PaymentStatusUpdateSerializer, StaffSerializerUpdateAccount
)

from .utils.notifications import send_sms

# =========================
# AUTHENTICATION
# =========================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "user": UserProfileSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            "message": "Registration successful"
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response({
            "user": UserProfileSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            "message": "Login successful"
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =========================
# USER PROFILE
# =========================

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def put(self, request):
        user = request.user

        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.email = request.data.get("email", user.email)
        user.save()

        if hasattr(user, "customer"):
            customer = user.customer
            customer.phone = request.data.get("phone", customer.phone)
            customer.address = request.data.get("address", customer.address)
            customer.name = f"{user.first_name} {user.last_name}"
            customer.save()

        elif hasattr(user, "staff"):
            staff = user.staff
            staff.phone = request.data.get("phone", staff.phone)
            staff.name = f"{user.first_name} {user.last_name}"
            staff.save()

        return Response(UserProfileSerializer(user).data)


# =========================
# VALIDATION UTILITIES
# =========================

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def check_username(request):
    username = request.data.get("username")
    exists = User.objects.filter(username=username).exists()
    return Response({"exists": exists})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def check_email(request):
    email = request.data.get("email")
    exists = User.objects.filter(email=email).exists()
    return Response({"exists": exists})

@api_view(['PATCH'])
@permission_classes([permissions.AllowAny])
def update_order_status(request, pk):
    """
    Update order status only.
    """
    order = get_object_or_404(Order, id=pk)
    new_status = request.data.get("status")

    if new_status not in ['pending','processing','ready','delivered','cancelled']:
        return Response({"detail":"Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    order.status = new_status
    order.save(update_fields=["status"])

    # ✅ Send SMS when ready
    if new_status == "ready" and order.customer:
        customer = order.customer  # Assuming order.customer is a ForeignKey to Customer
        phone = customer.phone
        if phone:
            message = (
                f"Hello {customer.name}, your laundry order #{order.order_number} "
                f"is ready for pickup/delivery. Thank you!"
            )
            send_sms(phone, message)

    return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([permissions.AllowAny])
def update_payment_status(request, pk):
    """
    Update payment status only.
    """
    payment = get_object_or_404(Payment, pk=pk)

    serializer = PaymentStatusUpdateSerializer(
        Payment,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=drf_status.HTTP_200_OK)

    return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)

api_view(['PATCH'])
@permission_classes([permissions.AllowAny])
def update_staff_account(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    serializer = StaffSerializerUpdateAccount(
        Staff,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=drf_status.HTTP_200_OK)

    return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)


# =========================
# CORE RESOURCES
# =========================

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

    def perform_create(self, serializer):
        # Save the serializer instance while injecting the current user
        serializer.save()



class GarmentTypeViewSet(viewsets.ModelViewSet):
    queryset = GarmentType.objects.all()
    serializer_class = GarmentTypeSerializer


class ServiceTypeViewSet(viewsets.ModelViewSet):
    queryset = ServiceType.objects.all()
    serializer_class = ServiceTypeSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer

    def perform_create(self, serializer):
        order = serializer.save()

        # # 🔔 EMIT REAL-TIME ADMIN NOTIFICATION
        # channel_layer = get_channel_layer()

        # async_to_sync(channel_layer.group_send)(
        #     "admin_notifications",
        #     {
        #         "type": "send_notification",
        #         "data": {
        #             "type": "NEW_ORDER",
        #             "order_id": order.id,
        #             "customer": order.customer.name,
        #             "total": str(order.total_amount),
        #             "delivery_type": order.delivery_type,
        #             "created_at": order.created_at.isoformat(),
        #         },
        #     },
        # )

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        return Response({
            "total_orders": Order.objects.count(),
            "pending_orders": Order.objects.filter(status="pending").count(),
            "processing_orders": Order.objects.filter(status="processing").count(),
            "total_revenue": float(
                Order.objects.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
            )
        })


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-issued_date')
    serializer_class = InvoiceSerializer
    
    @action(detail=True, methods=['get'])
    def payment_history(self, request, pk=None):
        """Get all payments for this invoice"""
        invoice = self.get_object()
        payments = invoice.payments.all().order_by('-payment_date')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-payment_date')
    serializer_class = PaymentSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        total_payments = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        pending_payments = Payment.objects.filter(status='pending').count()
        
        return Response({
            'total_payments': float(total_payments),
            'pending_payments': pending_payments
        })
    
    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        """Get receipt for this payment"""
        payment = self.get_object()
        if hasattr(payment, 'receipt'):
            serializer = ReceiptSerializer(payment.receipt)
            return Response(serializer.data)
        return Response({'error': 'Receipt not found'}, status=404)
    

class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for receipts (they're auto-generated)"""
    queryset = Receipt.objects.all().order_by('-generated_date')
    serializer_class = ReceiptSerializer


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all().order_by("-created_at")
    serializer_class = FeedbackSerializer

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        return Response({
            "average_rating": round(
                Feedback.objects.aggregate(Avg("rating"))["rating__avg"] or 0, 2
            ),
            "total_feedbacks": Feedback.objects.count(),
            "rating_distribution": list(
                Feedback.objects.values("rating").annotate(count=Count("rating"))
            )
        })


class AssignOrderStaffView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        # Permission: manager or superuser
        if not request.user.is_superuser:
            try:
                staff_profile = request.user.staff
            except Staff.DoesNotExist:
                return Response(
                    {"detail": "You are not allowed to assign orders."},
                    status=status.HTTP_403_FORBIDDEN
                )

            if staff_profile.role != "manager":
                return Response(
                    {"detail": "Only managers can assign orders."},
                    status=status.HTTP_403_FORBIDDEN
                )

        staff_id = request.data.get("staff_id")
        assign_type = request.data.get("type")  # washer | ironer

        if assign_type not in ["washer", "ironer"]:
            return Response(
                {"detail": "Invalid assignment type."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Unassign
        if staff_id is None:
            if assign_type == "washer":
                order.assigned_washer = None
            else:
                order.assigned_ironer = None

            order.save()
            return Response({"detail": "Order unassigned successfully"})

        # Assign
        staff = get_object_or_404(
            Staff,
            id=staff_id,
            role=assign_type,
            is_active=True
        )

        if assign_type == "washer":
            order.assigned_washer = staff
        else:
            order.assigned_ironer = staff

        order.save()

        return Response({
            "detail": "Order assigned successfully",
            "type": assign_type,
            "staff_id": staff.id,
            "staff_name": staff.name,
        })
