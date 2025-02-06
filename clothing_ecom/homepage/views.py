from django.shortcuts import render
from .models import Product
# Create your views here.
def home(request):
    new_arrivals = Product.objects.order_by('-created_at')[:6]
    sale_products = Product.objects.order_by('-created_at')[:6]

    return render(request, 'homepage/index.html',{
        'new_arrivals':new_arrivals,
        'sale_products':sale_products
    })