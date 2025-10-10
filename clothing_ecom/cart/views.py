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
from django.db import IntegrityError
import shortuuid

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
    cart_item = CartItem.objects.all().count()
    if cart_item >0:
        total_price = sum(item.total_price() for item in cart_items)
        amount = total_price
        tax_amount = 10
        total_amount = amount+tax_amount
        transaction_uuid = shortuuid.uuid()
        return render(request,"cart/checkout.html", {
            'amount':amount,
            'tax_amount':tax_amount,
            'total_amount': total_amount,
            'transaction_uuid': transaction_uuid,
        })
    else:
        return render(request, 'homepage/errorpage.html', {
            'error_message': 'No items in cart.'
        })
        

def buy(request, product_id):
    product = get_object_or_404(Product, id=product_id) #individual product fetching
    if product.quantity_available <= 0:
        messages.error(request, f"The product {product.name} is out of stock.")
        return redirect(reverse("home"))
    add_to_cart(request,product.id)
    amount = product.price
    tax_rate = Decimal('0.1')
    tax_amount = amount*tax_rate
    total_amount = amount+tax_amount
    transaction_uuid = shortuuid.uuid()
    return render(request, "cart/checkout.html",{
        'amount':amount,
        'tax_amount':tax_amount,
        'total_amount':total_amount,
        'transaction_uuid': transaction_uuid,
    })

SECRET_KEY = "8gBm/:&EnhH.1/q"


import requests
from .models import PaymentTransaction
#     e
secret_key = "8gBm/:&EnhH.1/q"
def generate_signature(secret_key, total_amount, transaction_uuid, product_code):
    # Prepare the signature string, formatted the same as in JavaScript
    signature_string = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    ss = signature_string.encode('utf-8')
    sk = secret_key.encode('utf-8')
    # Create the HMAC hash using the secret key and the signature string
    hmac_hash = hmac.new(sk, ss, hashlib.sha256)
    digest =hmac_hash.digest()
    # Base64 encode the result
    signature = base64.b64encode(digest).decode('utf-8')
    
    return signature


def success_payment(request):
    
    encoded_response = request.GET.get('data', '')
    
    if not encoded_response:
        return JsonResponse({'error': 'No response received from eSewa'}, status=400)
    
    # Step 1: Decode the Base64 encoded response
    decoded_response = base64.b64decode(encoded_response).decode('utf-8')
    response_data = json.loads(decoded_response)
    
    transaction_code = response_data.get('transaction_code')
    status = response_data.get('status')
    total_amount = response_data.get('total_amount')
    signature = response_data.get('signature')
    print("Signature unraveled from response body:",signature)
    transaction_uuid = response_data.get('transaction_uuid')
    product_code = response_data.get('product_code')
    print("Product code:",product_code)
    payment_transaction = PaymentTransaction(
        transaction_uuid=transaction_code,
        product_code='EPAYTEST',  # This is the product code, adjust as necessary
        total_amount=total_amount,
        status=status,
        ref_id=response_data.get('ref_id')  # If available
    )
    try:
        payment_transaction.save()
    except IntegrityError as e:
        print(f"Error: {e}")

        # Redirect to the error page in case of IntegrityError
        return render(request, 'homepage/errorpage.html', {
            'error_message': 'A unique constraint error occurred. Please try again.'
        })

    # Call the transaction status API to verify the transaction
    # transaction_status = get_transaction_status(transaction_code, 'EPAYTEST', total_amount)

    if status == 'COMPLETE':
        # Process the payment and decrease the product quantities
        cart_items = CartItem.objects.filter(user=request.user)
        try:
            with transaction.atomic():  # Ensure atomicity of the payment process
                for cart_item in cart_items:
                    # product = cart_item.product
                    # Update product quantity (decrease by quantity in cart)
                    # if product.quantity_available >= cart_item.quantity:
                        # product.quantity_available -= cart_item.quantity
                        # product.save()

                        # Update CartItem quantity to reflect the actual purchase
                    cart_item.quantity -= cart_item.quantity  # Set it to zero or the actual purchased quantity
                    cart_item.save()
                    if cart_item.quantity == 0:
                        cart_item.delete()

                    # else:
                        # If there's not enough stock, raise an exception
                        # raise ValueError(f"Not enough stock for product {product.name}.")
                
                # Return a success response to the 'view_cart' or a success page
                return render(request,'cart/payment_success.html', {'transaction_code':transaction_code, 'total_amount':total_amount})

        except ValueError as e:
            # If there's an issue (e.g., not enough stock), handle the exception
            return JsonResponse({'error': str(e)}, status=400)
    else:
        # Handle unsuccessful payment verification
        return JsonResponse({'error': 'Payment status verification failed'}, status=400)

import requests
from django.http import JsonResponse

def failure_payment(request):
    # Retrieve transaction details from the request (if available)
    transaction_uuid = request.GET.get('transaction_uuid')
    total_amount = request.GET.get('total_amount')
    product_code = request.GET.get('product_code')

    if not transaction_uuid:
        return JsonResponse({'error': 'Missing transaction_uuid'}, status=400)
    if not total_amount:
        return JsonResponse({'error': 'Missing total_amount '}, status=400)
    if not product_code:
        return JsonResponse({'error': 'Missing product_code '}, status=400)

    # Call eSewa's status check API
    status_check_url = f"https://rc.esewa.com.np/api/epay/transaction/status/?product_code={product_code}&total_amount={total_amount}&transaction_uuid={transaction_uuid}"
    response = requests.get(status_check_url)

    if response.status_code != 200:
        return JsonResponse({'error': 'Error checking transaction status'}, status=500)

    # Parse the response
    response_data = response.json()
    status = response_data.get('status')
    payment_transaction = PaymentTransaction(
        transaction_uuid=transaction_uuid,
        product_code=product_code,  # This is the product code, adjust as necessary
        total_amount=total_amount,
        status=status,
        ref_id=response_data.get('ref_id')  # If available
    )
    try:
        payment_transaction.save()
    except IntegrityError as e:
        print(f"Error: {e}")

        # Redirect to the error page in case of IntegrityError
        return render(request, 'homepage/errorpage.html', {
            'error_message': 'A unique constraint error occurred. Please try again.'
        })


    if status == 'PENDING':
        # Handle the case where payment is still pending
        return render(request, 'homepage/errorpage.html', {
            'error_message': 'Payment initiated but not completed yet. Please try again later.'
        })

    elif status == 'FULL_REFUND':
        # Handle the case where full payment was refunded
        return render(request, 'homepage/errorpage.html', {
            'error_message': 'Full payment was refunded to the customer.'
        })

    elif status == 'PARTIAL_REFUND':
        # Handle the case where partial payment was refunded
        return render(request, 'homepage/errorpage.html', {
            'error_message': 'Partial payment was refunded to the customer.'
        })

    elif status == 'AMBIGUOUS':
        # Handle the case where payment is in an ambiguous state
        return render(request, 'homepage/errorpage.html', {
            'error_message': 'Payment is in an ambiguous state.'
        })

    elif status == 'NOT_FOUND':
        # Handle the case where payment session has expired
        return render(request, 'homepage/errorpage.html', {
            'error_message': 'Payment session expired, not found.'
        })

    elif status == 'CANCELED':
        # Handle the case where payment was canceled/reversed
        return render(request, 'homepage/errorpage.html', {
            'error_message': 'Payment was canceled or reversed by eSewa.'
        })

    else:
        # If none of the above statuses match, handle the server unavailability
        error_message = response_data.get('error_message', 'Unknown error occurred.')
        return render(request, 'homepage/errorpage.html', {
            'error_message': error_message
        })