from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Staff(models.Model):
    ROLE_CHOICES = [
        ('washer', 'Washer'),
        ('ironer', 'Ironer'),
        ('delivery', 'Delivery'),
        ('manager', 'Manager'),
    ]
    
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.role})"

class GarmentType(models.Model):
    GARMENT_CHOICES = [
        ('native_wear', 'Native Wears'),
        ('english_wear', 'English Wears'),
        ('bed_sheet', 'Bed Sheet'),
        ('agbada', 'Agbada'),
    ]
    
    name = models.CharField(max_length=50, choices=GARMENT_CHOICES, unique=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.get_name_display()

class ServiceType(models.Model):
    SERVICE_CHOICES = [
        ('regular', 'Regular'),
        ('express', 'Express'),
    ]
    
    name = models.CharField(max_length=20, choices=SERVICE_CHOICES, unique=True)
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.get_name_display()

class Order(models.Model):
    DELIVERY_CHOICES = [
        ('pickup', 'Pickup'),
        ('byself', 'By Self'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_CHOICES)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    assigned_washer = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="washing_orders"
    )

    assigned_ironer = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ironing_orders"
    )
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.delivery_fee = Decimal('500.00') if self.delivery_type == 'pickup' else Decimal('0.00')
        self.total_amount = self.subtotal + self.delivery_fee
        self.save()
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    garment_type = models.ForeignKey(GarmentType, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        base_price = self.garment_type.base_price
        service_multiplier = self.order.service_type.price_multiplier
        self.unit_price = base_price * service_multiplier
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        self.order.calculate_total()
    
    def __str__(self):
        return f"{self.garment_type.name} x {self.quantity}"

class Invoice(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid in Full'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    issued_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV{timezone.now().strftime('%Y%m%d%H%M%S')}"
        if not self.due_date:
            self.due_date = (timezone.now() + timezone.timedelta(days=7)).date()
        # Initialize balance_due on first save
        if not self.pk and hasattr(self, 'order'):
            self.balance_due = self.order.total_amount
        super().save(*args, **kwargs)
    
    def update_payment_status(self):
        """Update payment status based on completed payments"""
        total_amount = self.order.total_amount
        self.amount_paid = sum(
            payment.amount for payment in self.payments.filter(status='completed')
        )
        self.balance_due = total_amount - self.amount_paid
        
        if self.amount_paid == 0:
            self.payment_status = 'unpaid'
        elif self.amount_paid >= total_amount:
            self.payment_status = 'paid'
            self.balance_due = Decimal('0.00')
        else:
            self.payment_status = 'partial'
        
        self.save()
    
    def __str__(self):
        return f"{self.invoice_number} - {self.order.order_number}"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            old_payment = Payment.objects.get(pk=self.pk)
            old_status = old_payment.status
        
        super().save(*args, **kwargs)
        
        # Update invoice payment status after saving
        self.invoice.update_payment_status()
        
        # Auto-generate receipt when payment is completed
        if self.status == 'completed' and old_status != 'completed':
            if not hasattr(self, 'receipt'):
                Receipt.objects.create(payment=self)
    
    def __str__(self):
        return f"Payment for {self.invoice.invoice_number} - ₦{self.amount}"

class Receipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=20, unique=True, editable=False)
    generated_date = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"RCT{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.receipt_number} - {self.payment.invoice.invoice_number}"

class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='feedbacks')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback from {self.customer.name} - {self.rating} stars"
