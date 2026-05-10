from django.contrib import admin
from .models import (
    Customer, Staff, GarmentType, ServiceType,
    Order, OrderItem, Invoice, Payment, Feedback
)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'created_at']
    search_fields = ['name', 'email', 'phone']
    list_filter = ['created_at']

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'phone', 'is_active', 'created_at']
    search_fields = ['name', 'phone']
    list_filter = ['role', 'is_active', 'created_at']

@admin.register(GarmentType)
class GarmentTypeAdmin(admin.ModelAdmin):
    list_display = ['get_name_display', 'base_price']
    list_editable = ['base_price']

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['get_name_display', 'price_multiplier']
    list_editable = ['price_multiplier']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ['unit_price', 'total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'service_type', 'delivery_type', 'total_amount', 'status', 'created_at']
    search_fields = ['order_number', 'customer__name']
    list_filter = ['status', 'service_type', 'delivery_type', 'created_at']
    readonly_fields = ['order_number', 'subtotal', 'total_amount', 'delivery_fee']
    inlines = [OrderItemInline]

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'order', 'issued_date', 'due_date']
    search_fields = ['invoice_number', 'order__order_number']
    list_filter = ['issued_date', 'due_date']
    readonly_fields = ['invoice_number', 'issued_date']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_method', 'status', 'payment_date']
    search_fields = ['invoice__invoice_number', 'transaction_reference']
    list_filter = ['status', 'payment_method', 'payment_date']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['customer', 'order', 'rating', 'created_at']
    search_fields = ['customer__name', 'order__order_number']
    list_filter = ['rating', 'created_at']
    readonly_fields = ['created_at']