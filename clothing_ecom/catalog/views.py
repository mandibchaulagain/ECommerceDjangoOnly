from django.shortcuts import get_object_or_404, render
from homepage.models import Product
# Create your views here.
def mensClothing(request):
    products = Product.objects.filter(category="Men")
    
    return render(request, "catalog/mensClothes.html", {'products':products})