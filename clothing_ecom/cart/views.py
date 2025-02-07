from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import urllib
from .models import CartItem
from homepage.models import Product
from django.urls import reverse
from decimal import Decimal
from django.contrib import messages
from django.http import JsonResponse
import base64
import json
import hmac
import hashlib
from django.db import transaction

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.quantity_available <= 0:
        messages.error(request, f"The product {product.name} is out of stock.")
        return redirect(reverse("view_cart"))
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        
    product.quantity_available-=1
    product.save()

    return redirect(reverse("view_cart"))

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.total_price() for item in cart_items)

    return render(request, "cart/cart.html", {"cart_items": cart_items, "total_price": total_price})

@login_required
def remove_from_cart(request, cart_item_id, product_id, quantity):
    try:
        cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
        cart_item.delete()
        product = get_object_or_404(Product, id=product_id)
        product.quantity_available+=quantity
        product.save()
        messages.success(request, "Item successfully removed from your cart.")
    except CartItem.DoesNotExist:
        messages.error(request, "The item you're trying to remove was not found in your cart.")
    
    return redirect("view_cart")

# Increase the quantity of a cart item
def increase_quantity(request, cart_item_id,product_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    cart_item.quantity += 1  # Increase quantity by 1
    cart_item.save()
    product = get_object_or_404(Product,id= product_id)
    product.quantity_available-=1
    product.save()
    messages.success(request, f"Quantity of {cart_item.product.name} increased.")
    return redirect("view_cart")

# Decrease the quantity of a cart item (but not below 1)
def decrease_quantity(request, cart_item_id,product_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    product = get_object_or_404(Product,id=product_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1  # Decrease quantity by 1
        cart_item.save()
        product.quantity_available+=1
        product.save()

        messages.success(request, f"Quantity of {cart_item.product.name} decreased.")
    else:
        messages.warning(request, f"Cannot decrease quantity below 1 for {cart_item.product.name}.")
    
    return redirect("view_cart")

def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.total_price() for item in cart_items)
    amount = total_price
    tax_amount = 10
    total_amount = amount+tax_amount
    return render(request,"cart/checkout.html", {
        'amount':amount,
        'tax_amount':tax_amount,
        'total_amount': total_amount,
        
    })

def buy(request, product_id):
    product = get_object_or_404(Product, id=product_id) #individual product fetching
    if product.quantity_available <= 0:
        messages.error(request, f"The product {product.name} is out of stock.")
        return redirect(reverse("home"))
    amount = product.price
    tax_rate = Decimal('0.1')
    tax_amount = amount*tax_rate
    total_amount = amount+tax_amount
    return render(request, "cart/checkout.html",{
        'amount':amount,
        'tax_amount':tax_amount,
        'total_amount':total_amount,
    })

SECRET_KEY = "8gBm/:&EnhH.1/q"

def success_payment(request):
    # Get the response body (Base64 encoded)
    encoded_response = request.GET.get('data', '')
    
    if not encoded_response:
        return JsonResponse({'error': 'No response received from eSewa'}, status=400)
    
    # Step 1: Decode the Base64 encoded response
    decoded_response = base64.b64decode(encoded_response).decode('utf-8')
    response_data = json.loads(decoded_response)
    
    transaction_code = response_data.get('transaction_code')
    status = response_data.get('status')
    total_amount = response_data.get('total_amount')

    # Step 3: Verify if the payment status is COMPLETE
    if status != 'COMPLETE':
        return JsonResponse({'error': 'Payment was not completed'}, status=400)
    
    # Step 5: Process the payment and decrease the product quantities
    cart_items = CartItem.objects.filter(user=request.user)
    # is_paid=False
    
    try:
        with transaction.atomic():  # Ensure atomicity of the payment process
            for cart_item in cart_items:
                product = cart_item.product
                # Update product quantity (decrease by quantity in cart)
                if product.quantity_available >= cart_item.quantity:
                    product.quantity_available -= cart_item.quantity
                    product.save()
                    
                    # Update CartItem quantity to reflect the actual purchase
                    cart_item.quantity -= cart_item.quantity  # Set it to zero or the actual purchased quantity
                    cart_item.save()
                    if cart_item.quantity ==0:
                        cart_item.delete()

                else:
                    # If there's not enough stock, raise an exception
                    raise ValueError(f"Not enough stock for product {product.name}.")
            
            # Step 6: Mark CartItems as paid
            # cart_items.update(is_paid=True) i dont have is_paid in my model
            
            # Return a success response after processing the payment
            # return render(request, 'cart/payment_success.html', {
            #     'transaction_code': transaction_code,
            #     'total_amount': total_amount
            # })
            return redirect('view_cart')

    except ValueError as e:
        # If there's an issue (e.g., not enough stock), handle the exception
        return JsonResponse({'error': str(e)}, status=400)