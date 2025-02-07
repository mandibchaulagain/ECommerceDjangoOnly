from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    category = models.CharField(max_length=100, choices = [
        ('Men','Men'),
        ('Women', 'Women'),
        ('Accessories', 'Accessories'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    quantity_available = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.name