from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from laundry_api.models import (
    Customer, Staff, GarmentType, ServiceType,
    Order, OrderItem, Invoice, Payment, Feedback
)
from decimal import Decimal
import random
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Populates the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database population...')
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        self.stdout.write('Clearing existing data...')
        Feedback.objects.all().delete()
        Payment.objects.all().delete()
        Invoice.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Staff.objects.all().delete()
        Customer.objects.all().delete()
        ServiceType.objects.all().delete()
        GarmentType.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        
        # Create Garment Types
        self.stdout.write('Creating garment types...')
        garment_types = [
            GarmentType.objects.create(
                name='native_wear',
                base_price=Decimal('1500.00'),
                description='Traditional Nigerian native wears including buba, sokoto, and wrapper'
            ),
            GarmentType.objects.create(
                name='english_wear',
                base_price=Decimal('1000.00'),
                description='Western clothing including shirts, trousers, and dresses'
            ),
            GarmentType.objects.create(
                name='bed_sheet',
                base_price=Decimal('800.00'),
                description='Bed sheets, pillow cases, and bed linens'
            ),
            GarmentType.objects.create(
                name='agbada',
                base_price=Decimal('2500.00'),
                description='Traditional Agbada ceremonial wear'
            ),
        ]
        self.stdout.write(self.style.SUCCESS(f'Created {len(garment_types)} garment types'))
        
        # Create Service Types
        self.stdout.write('Creating service types...')
        service_regular = ServiceType.objects.create(
            name='regular',
            price_multiplier=Decimal('1.0'),
            description='Standard laundry service - Ready in 3-5 days'
        )
        service_express = ServiceType.objects.create(
            name='express',
            price_multiplier=Decimal('2.0'),
            description='Express laundry service - Ready in 24 hours'
        )
        self.stdout.write(self.style.SUCCESS('Created 2 service types'))
        
        # Create Customers
        self.stdout.write('Creating customers...')
        customers_data = [
            {'name': 'Adewale Johnson', 'email': 'adewale.johnson@email.com', 'phone': '08012345678', 'address': '123 Allen Avenue, Ikeja, Lagos'},
            {'name': 'Chidinma Okafor', 'email': 'chidinma.okafor@email.com', 'phone': '08023456789', 'address': '45 Ahmadu Bello Way, Victoria Island, Lagos'},
            {'name': 'Ibrahim Musa', 'email': 'ibrahim.musa@email.com', 'phone': '08034567890', 'address': '78 Kano Road, Kano'},
            {'name': 'Blessing Eze', 'email': 'blessing.eze@email.com', 'phone': '08045678901', 'address': '12 Independence Way, Enugu'},
            {'name': 'Yusuf Abdullahi', 'email': 'yusuf.abdullahi@email.com', 'phone': '08056789012', 'address': '34 Ahmadu Bello Road, Kaduna'},
            {'name': 'Funmilayo Adebayo', 'email': 'funmilayo.adebayo@email.com', 'phone': '08067890123', 'address': '56 Ring Road, Ibadan'},
            {'name': 'Emeka Nwankwo', 'email': 'emeka.nwankwo@email.com', 'phone': '08078901234', 'address': '89 Aba Road, Port Harcourt'},
            {'name': 'Aisha Bello', 'email': 'aisha.bello@email.com', 'phone': '08089012345', 'address': '23 Constitution Avenue, Abuja'},
            {'name': 'Oluwaseun Oladipo', 'email': 'oluwaseun.oladipo@email.com', 'phone': '08090123456', 'address': '67 Broad Street, Lagos Island'},
            {'name': 'Ngozi Onyeka', 'email': 'ngozi.onyeka@email.com', 'phone': '08101234567', 'address': '90 Awolowo Road, Ikoyi, Lagos'},
        ]
        
        customers = []
        for customer_data in customers_data:
            # Create user account for customer
            username = customer_data['name'].lower().replace(' ', '_')
            try:
                user = User.objects.create_user(
                    username=username,
                    email=customer_data['email'],
                    password='password123',
                    first_name=customer_data['name'].split()[0],
                    last_name=' '.join(customer_data['name'].split()[1:])
                )
                customer = Customer.objects.create(user=user, **customer_data)
                customers.append(customer)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not create customer {username}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(customers)} customers'))
        
        # Create Staff
        self.stdout.write('Creating staff members...')
        staff_data = [
            {'name': 'Mohammed Hassan', 'role': 'manager', 'phone': '08011111111'},
            {'name': 'Grace Okonkwo', 'role': 'washer', 'phone': '08022222222'},
            {'name': 'Tunde Bakare', 'role': 'washer', 'phone': '08033333333'},
            {'name': 'Fatima Aliyu', 'role': 'ironer', 'phone': '08044444444'},
            {'name': 'Peter Obi', 'role': 'ironer', 'phone': '08055555555'},
            {'name': 'Kemi Adeleke', 'role': 'delivery', 'phone': '08066666666'},
            {'name': 'Chukwudi Ibe', 'role': 'delivery', 'phone': '08077777777'},
        ]
        
        staff_members = []
        for i, staff_info in enumerate(staff_data):
            username = staff_info['name'].lower().replace(' ', '_')
            user = User.objects.create_user(
                username=username,
                email=f"{username}@laundry.com",
                password='password123'
            )
            staff = Staff.objects.create(
                user=user,
                name=staff_info['name'],
                role=staff_info['role'],
                phone=staff_info['phone'],
                is_active=True
            )
            staff_members.append(staff)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(staff_members)} staff members'))
        
        # Create Orders with Items
        self.stdout.write('Creating orders...')
        order_statuses = ['pending', 'processing', 'ready', 'delivered', 'delivered']
        delivery_types = ['pickup', 'byself']
        
        orders = []
        for i in range(20):
            # Random date in the last 30 days
            days_ago = random.randint(0, 30)
            created_date = timezone.now() - timedelta(days=days_ago)
            
            customer = random.choice(customers)
            service_type = random.choice([service_regular, service_express])
            delivery_type = random.choice(delivery_types)
            status = random.choice(order_statuses)
            
            order = Order.objects.create(
                customer=customer,
                service_type=service_type,
                delivery_type=delivery_type,
                status=status,
                notes=random.choice([
                    'Please handle with care',
                    'Stain on collar, please pay attention',
                    'Express service needed for event',
                    '',
                    'Delicate fabric',
                ])
            )
            
            # Set the created_at date
            order.created_at = created_date
            order.save()
            
            # Add 1-4 random items to each order
            num_items = random.randint(1, 4)
            selected_garments = random.sample(garment_types, num_items)
            
            for garment in selected_garments:
                quantity = random.randint(1, 5)
                OrderItem.objects.create(
                    order=order,
                    garment_type=garment,
                    quantity=quantity
                )
            
            orders.append(order)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(orders)} orders with items'))
        
        # Create Invoices (automatically created, but let's verify)
        self.stdout.write('Verifying invoices...')
        invoices = []
        for order in orders:
            invoice, created = Invoice.objects.get_or_create(
                order=order,
                defaults={'due_date': (order.created_at + timedelta(days=7)).date()}
            )
            invoice.issued_date = order.created_at
            invoice.save()
            invoices.append(invoice)
        
        self.stdout.write(self.style.SUCCESS(f'Verified {len(invoices)} invoices'))
        
        # Create Payments
        self.stdout.write('Creating payments...')
        payment_methods = ['cash', 'card', 'transfer']
        payment_statuses = ['completed', 'completed', 'completed', 'pending', 'failed']
        
        payments = []
        for invoice in invoices:
            # 80% of orders have payments
            if random.random() < 0.8:
                payment_status = random.choice(payment_statuses)
                payment_date = invoice.order.created_at + timedelta(days=random.randint(0, 5))
                
                payment = Payment.objects.create(
                    invoice=invoice,
                    amount=invoice.order.total_amount,
                    payment_method=random.choice(payment_methods),
                    status=payment_status,
                    transaction_reference=f'TXN{random.randint(100000, 999999)}' if payment_status != 'cash' else '',
                    notes=random.choice([
                        'Payment received',
                        'Online payment',
                        'Cash on delivery',
                        '',
                    ])
                )
                payment.payment_date = payment_date
                payment.save()
                payments.append(payment)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(payments)} payments'))
        
        # Create Feedback for delivered orders
        self.stdout.write('Creating customer feedback...')
        feedback_comments = [
            "Excellent service! My clothes came back spotless and smelling fresh.",
            "Very satisfied with the quality. Will definitely use again.",
            "Good service but took longer than expected.",
            "Professional and reliable. The express service is worth it!",
            "Clothes were well pressed and neatly packaged.",
            "Outstanding attention to detail. Very impressed!",
            "Average service. Nothing special but got the job done.",
            "Fast and efficient. Love the convenience of home pickup.",
            "Great value for money. Highly recommend!",
            "The staff was very courteous and professional.",
            "My agbada was beautifully cleaned and pressed.",
            "Satisfied with the service. Will be a regular customer.",
            "Quick turnaround time. Very pleased!",
            "Good experience overall. A few minor issues but nothing major.",
            "Fantastic service! Best laundry in town!",
        ]
        
        delivered_orders = Order.objects.filter(status='delivered')
        feedbacks = []
        
        for order in delivered_orders:
            # 70% of delivered orders have feedback
            if random.random() < 0.7:
                rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 30, 40])[0]
                feedback = Feedback.objects.create(
                    customer=order.customer,
                    order=order,
                    rating=rating,
                    comment=random.choice(feedback_comments)
                )
                feedback.created_at = order.created_at + timedelta(days=random.randint(1, 3))
                feedback.save()
                feedbacks.append(feedback)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(feedbacks)} feedback entries'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Database Population Complete ==='))
        self.stdout.write(self.style.SUCCESS(f'Garment Types: {GarmentType.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Service Types: {ServiceType.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Customers: {Customer.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Staff: {Staff.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Orders: {Order.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Order Items: {OrderItem.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Invoices: {Invoice.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Payments: {Payment.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Feedback: {Feedback.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('\nYou can now login to the admin panel or use the frontend!'))
        self.stdout.write(self.style.WARNING('Staff login credentials:'))
        self.stdout.write(self.style.WARNING('Username: mohammed_hassan (or any staff name with underscore)'))
        self.stdout.write(self.style.WARNING('Password: password123'))