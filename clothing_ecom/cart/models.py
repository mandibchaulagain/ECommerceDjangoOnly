from django.db import models
from homepage.models import Product
from django.contrib.auth.models import User
    
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.product.price * self.quantity
    
class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),#PENDING saved in the database, but Pending shown to user
        ('COMPLETE', 'Complete'),
        ('FULL_REFUND', 'Full Refund'),
        ('PARTIAL_REFUND', 'Partial Refund'),
        ('AMBIGUOUS', 'Ambiguous'),
        ('NOT_FOUND', 'Not Found'),
        ('CANCELED', 'Canceled'),
        ('FAILED', 'Failed'),
    ]
    transaction_uuid = models.CharField(max_length=255, unique=True)
    product_code = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    ref_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Transaction {self.transaction_uuid} - {self.status}"