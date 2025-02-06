from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
from homepage.models import Product
from django.urls import reverse

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if the product is already in the cart for the logged-in user
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    
    if not created:  # If item already exists, just increase quantity
        cart_item.quantity += 1
        cart_item.save()

    return redirect(reverse("view_cart"))

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.total_price() for item in cart_items)

    return render(request, "cart/cart.html", {"cart_items": cart_items, "total_price": total_price})

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    cart_item.delete()
    return redirect("view_cart")

def checkout(request):
    return render(request,"cart/checkout.html")