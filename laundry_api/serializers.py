from rest_framework import serializers
from .models import (
    Customer, Staff, GarmentType, ServiceType, 
    Order, OrderItem, Invoice, Payment, Feedback, User, Receipt
)
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=['customer', 'admin'], default='customer')
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role', 'phone', 'address']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        role = validated_data.pop('role')
        phone = validated_data.pop('phone')
        address = validated_data.pop('address', '')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        if role == 'admin':
            user.is_staff = True
            user.save()
            Staff.objects.create(
                user=user,
                name=f"{user.first_name} {user.last_name}",
                role='manager',
                phone=phone
            )
        else:
            Customer.objects.create(
                user=user,
                name=f"{user.first_name} {user.last_name}",
                email=user.email,
                phone=phone,
                address=address
            )
        
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('Account is disabled')
        else:
            raise serializers.ValidationError('Must include username and password')
        
        attrs['user'] = user
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'profile']
    
    def get_role(self, obj):
        if obj.is_staff or obj.is_superuser:
            return 'admin'
        return 'customer'
    
    def get_profile(self, obj):
        try:
            if hasattr(obj, 'customer'):
                return CustomerSerializer(obj.customer).data
            elif hasattr(obj, 'staff'):
                return StaffSerializer(obj.staff).data
        except:
            pass
        return None

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = '__all__'


class StaffSerializerUpdateAccount(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['account_number']


class GarmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GarmentType
        fields = '__all__'

class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    garment_name = serializers.CharField(source='garment_type.get_name_display', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'garment_type', 'garment_name', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['unit_price', 'total_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    service_name = serializers.CharField(source='service_type.get_name_display', read_only=True)
    assigned_washer_name = serializers.CharField(
        source='assigned_washer.name',
        read_only=True,
        allow_null=True
    )
    assigned_ironer_name = serializers.CharField(
        source='assigned_ironer.name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number', 'subtotal', 'total_amount', 'delivery_fee']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # Auto-generate invoice
        Invoice.objects.create(order=order)
        
        return order
    

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

class InvoiceSerializer(serializers.ModelSerializer):
    order_details = OrderSerializer(source='order', read_only=True)
    customer_name = serializers.CharField(source='order.customer.name', read_only=True)
    total_amount = serializers.DecimalField(source='order.total_amount', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['invoice_number', 'issued_date', 'payment_status', 'amount_paid', 'balance_due']

class ReceiptSerializer(serializers.ModelSerializer):
    payment_details = serializers.SerializerMethodField()
    invoice_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Receipt
        fields = '__all__'
        read_only_fields = ['receipt_number', 'generated_date']
    
    def get_payment_details(self, obj):
        return {
            'amount': str(obj.payment.amount),
            'method': obj.payment.get_payment_method_display(),
            'status': obj.payment.get_status_display(),
            'date': obj.payment.payment_date,
            'reference': obj.payment.transaction_reference,
        }
    
    def get_invoice_details(self, obj):
        invoice = obj.payment.invoice
        return {
            'invoice_number': invoice.invoice_number,
            'order_number': invoice.order.order_number,
            'customer_name': invoice.order.customer.name,
            'total_amount': str(invoice.order.total_amount),
            'amount_paid': str(invoice.amount_paid),
            'balance_due': str(invoice.balance_due),
            'payment_status': invoice.get_payment_status_display(),
        }

class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    has_receipt = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = '__all__'
    
    def get_has_receipt(self, obj):
        return hasattr(obj, 'receipt')
    
    def create(self, validated_data):
        payment = Payment.objects.create(**validated_data)
        # Receipt is auto-generated in Payment.save() if status is completed
        return payment
    
    def update(self, instance, validated_data):
        # Payment.save() will handle receipt generation and invoice update
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
class PaymentStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

class FeedbackSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Feedback
        fields = '__all__'