from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Product
from cart.models import CartItem
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Product
from cart.models import CartItem, PaymentTransaction
import re

def home(request):
    """
    Homepage view that displays products organized by categories
    """
    # Get all products ordered by creation date
    all_products = Product.objects.order_by('-created_at')
    
    # Get products by category
    men_products = Product.objects.filter(category='Men').order_by('-created_at')
    women_products = Product.objects.filter(category='Women').order_by('-created_at')
    accessories_products = Product.objects.filter(category='Accessories').order_by('-created_at')
    
    # Get latest products for "Just Landed" section (mix of all categories)
    new_arrivals = Product.objects.order_by('-created_at')[:12]
    
    # Get all available categories for the filter
    categories = Product.objects.values_list('category', flat=True).distinct()
    
    # Get category counts for display on filter buttons
    category_counts = {
        'All': all_products.count(),
        'Men': men_products.count(),
        'Women': women_products.count(),
        'Accessories': accessories_products.count(),
    }
    
    # Note: cart_count is now handled by the context processor
    # No need to calculate it here anymore
    
    context = {
        'new_arrivals': new_arrivals,
        'all_products': all_products,
        'men_products': men_products,
        'women_products': women_products,
        'accessories_products': accessories_products,
        'categories': categories,
        'category_counts': category_counts,
    }
    
    return render(request, 'homepage/index.html', context)



def thankyoupage(request):
    """
    Thank you page after successful purchase
    """
    return render(request, "homepage/thankyoupage.html")

def product_detail(request, product_id):
    """
    Individual product detail page with related products
    """
    product = get_object_or_404(Product, id=product_id)
    
    # Get related products from the same category (excluding current product)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id).order_by('-created_at')[:8]
    
    # If not enough related products in same category, get from other categories
    if related_products.count() < 4:
        additional_products = Product.objects.exclude(
            id=product.id
        ).exclude(
            id__in=related_products.values_list('id', flat=True)
        ).order_by('-created_at')[:8-related_products.count()]
        
        related_products = list(related_products) + list(additional_products)
    
    # Check if user has this item in cart (for authenticated users)
    in_cart = False
    cart_quantity = 0
    if request.user.is_authenticated:
        try:
            cart_item = CartItem.objects.get(user=request.user, product=product)
            in_cart = True
            cart_quantity = cart_item.quantity
        except CartItem.DoesNotExist:
            pass
    
    # Calculate stock status
    stock_status = "In Stock"
    stock_class = "text-green-600"
    if product.quantity_available == 0:
        stock_status = "Out of Stock"
        stock_class = "text-red-600"
    elif product.quantity_available <= 5:
        stock_status = f"Only {product.quantity_available} left!"
        stock_class = "text-orange-600"
    
    context = {
        'product': product,
        'related_products': related_products,
        'in_cart': in_cart,
        'cart_quantity': cart_quantity,
        'stock_status': stock_status,
        'stock_class': stock_class,
    }
    
    return render(request, 'homepage/product_detail.html', context)

def subscribe_newsletter(request):
    """Handle newsletter subscription"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        # Validate email
        if not email:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please enter an email address.'})
            messages.error(request, 'Please enter an email address.')
            return redirect('home')
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'})
            messages.error(request, 'Please enter a valid email address.')
            return redirect('home')
        
        try:
            # Send notification email to admin
            admin_subject = 'New Newsletter Subscription - StyleHub'
            admin_message = f"""
New newsletter subscription received:

Email: {email}
Date: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}
IP Address: {get_client_ip(request)}

Best regards,
StyleHub System
            """
            
            send_mail(
                admin_subject,
                admin_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.NEWSLETTER_EMAIL],
                fail_silently=False,
            )
            
            # Send confirmation email to subscriber
            subscriber_subject = 'Welcome to StyleHub Newsletter!'
            subscriber_message = f"""
Hi there!

Thank you for subscribing to the StyleHub newsletter! 🎉

You'll be the first to know about:
• New product arrivals
• Exclusive sales and discounts
• Fashion trends and styling tips
• Special member-only offers

We're excited to have you as part of the StyleHub community!

If you have any questions, feel free to reply to this email.

Best regards,
The StyleHub Team

---
StyleHub - Your Fashion Destination
Website: {request.build_absolute_uri('/')}
            """
            
            send_mail(
                subscriber_subject,
                subscriber_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,  # Don't fail if subscriber email fails
            )
            
            # Success response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Thank you for subscribing! Check your email for confirmation.'})
            messages.success(request, 'Thank you for subscribing! Check your email for confirmation.')
            return redirect('home')
            
        except Exception as e:
            # Log the error (in production, use proper logging)
            print(f"Newsletter subscription error: {str(e)}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Sorry, there was an error processing your subscription. Please try again later.'})
            messages.error(request, 'Sorry, there was an error processing your subscription. Please try again later.')
            return redirect('home')
    
    # If not POST request, redirect to home
    return redirect('home')

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip