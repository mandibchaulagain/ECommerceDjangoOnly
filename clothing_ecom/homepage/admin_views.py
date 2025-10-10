from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from homepage.models import Product
from cart.models import PaymentTransaction
import json

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with overview statistics"""
    total_products = Product.objects.count()
    total_transactions = PaymentTransaction.objects.count()
    pending_transactions = PaymentTransaction.objects.filter(status='PENDING').count()
    completed_transactions = PaymentTransaction.objects.filter(status='COMPLETE').count()
    
    # Recent activity
    recent_products = Product.objects.order_by('-created_at')[:5]
    recent_transactions = PaymentTransaction.objects.order_by('-created_at')[:5]
    
    context = {
        'total_products': total_products,
        'total_transactions': total_transactions,
        'pending_transactions': pending_transactions,
        'completed_transactions': completed_transactions,
        'recent_products': recent_products,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def product_list(request):
    """Product list view with search, filter, and bulk actions"""
    products = Product.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category=category_filter)
    
    # Stock filter
    stock_filter = request.GET.get('stock', '')
    if stock_filter == 'low':
        products = products.filter(quantity_available__lte=5)
    elif stock_filter == 'out':
        products = products.filter(quantity_available=0)
    
    # Pagination
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter dropdown
    categories = Product.objects.values_list('category', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'stock_filter': stock_filter,
        'categories': categories,
        'total_count': products.count(),
    }
    
    return render(request, 'admin/product_list.html', context)

@login_required
@user_passes_test(is_admin)
def product_add(request):
    """Add new product"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category = request.POST.get('category')
        quantity_available = request.POST.get('quantity_available')
        image = request.FILES.get('image')
        
        try:
            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,
                quantity_available=quantity_available,
                image=image
            )
            messages.success(request, f'Product "{product.name}" was added successfully.')
            return redirect('admin_product_list')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
    
    categories = [choice[0] for choice in Product._meta.get_field('category').choices]
    return render(request, 'admin/product_form.html', {'categories': categories})

@login_required
@user_passes_test(is_admin)
def product_edit(request, product_id):
    """Edit existing product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.category = request.POST.get('category')
        product.quantity_available = request.POST.get('quantity_available')
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        try:
            product.save()
            messages.success(request, f'Product "{product.name}" was updated successfully.')
            return redirect('admin_product_list')
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    categories = [choice[0] for choice in Product._meta.get_field('category').choices]
    context = {
        'product': product,
        'categories': categories,
        'is_edit': True,
    }
    return render(request, 'admin/product_form.html', context)

@login_required
@user_passes_test(is_admin)
def product_delete(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" was deleted successfully.')
        return redirect('admin_product_list')
    
    return render(request, 'admin/product_confirm_delete.html', {'product': product})

@login_required
@user_passes_test(is_admin)
def product_bulk_action(request):
    """Handle bulk actions for products"""
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_products')
        
        if not selected_ids:
            messages.error(request, 'No products selected.')
            return redirect('admin_product_list')
        
        products = Product.objects.filter(id__in=selected_ids)
        
        if action == 'delete':
            count = products.count()
            products.delete()
            messages.success(request, f'{count} products were deleted successfully.')
        
        elif action == 'update_stock':
            new_stock = request.POST.get('new_stock', 0)
            products.update(quantity_available=new_stock)
            messages.success(request, f'Stock updated for {products.count()} products.')
        
        elif action == 'change_category':
            new_category = request.POST.get('new_category')
            if new_category:
                products.update(category=new_category)
                messages.success(request, f'Category updated for {products.count()} products.')
    
    return redirect('admin_product_list')

@login_required
@user_passes_test(is_admin)
def transaction_list(request):
    """Transaction list view with search, filter, and bulk actions"""
    transactions = PaymentTransaction.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        transactions = transactions.filter(
            Q(transaction_uuid__icontains=search_query) |
            Q(product_code__icontains=search_query) |
            Q(ref_id__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    # Date filter
    date_filter = request.GET.get('date_filter', '')
    if date_filter == 'today':
        transactions = transactions.filter(created_at__date=timezone.now().date())
    elif date_filter == 'week':
        week_ago = timezone.now() - timedelta(days=7)
        transactions = transactions.filter(created_at__gte=week_ago)
    elif date_filter == 'month':
        month_ago = timezone.now() - timedelta(days=30)
        transactions = transactions.filter(created_at__gte=month_ago)
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get status choices for filter dropdown
    status_choices = PaymentTransaction.STATUS_CHOICES
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': status_choices,
        'total_count': transactions.count(),
    }
    
    return render(request, 'admin/transaction_list.html', context)

@login_required
@user_passes_test(is_admin)
def transaction_add(request):
    """Add new transaction"""
    if request.method == 'POST':
        transaction_uuid = request.POST.get('transaction_uuid')
        product_code = request.POST.get('product_code')
        total_amount = request.POST.get('total_amount')
        status = request.POST.get('status')
        ref_id = request.POST.get('ref_id')
        
        try:
            transaction = PaymentTransaction.objects.create(
                transaction_uuid=transaction_uuid,
                product_code=product_code,
                total_amount=total_amount,
                status=status,
                ref_id=ref_id or None
            )
            messages.success(request, f'Transaction "{transaction.transaction_uuid}" was added successfully.')
            return redirect('admin_transaction_list')
        except Exception as e:
            messages.error(request, f'Error adding transaction: {str(e)}')
    
    status_choices = PaymentTransaction.STATUS_CHOICES
    return render(request, 'admin/transaction_form.html', {'status_choices': status_choices})

@login_required
@user_passes_test(is_admin)
def transaction_edit(request, transaction_id):
    """Edit existing transaction"""
    transaction = get_object_or_404(PaymentTransaction, id=transaction_id)
    
    if request.method == 'POST':
        transaction.transaction_uuid = request.POST.get('transaction_uuid')
        transaction.product_code = request.POST.get('product_code')
        transaction.total_amount = request.POST.get('total_amount')
        transaction.status = request.POST.get('status')
        transaction.ref_id = request.POST.get('ref_id') or None
        
        try:
            transaction.save()
            messages.success(request, f'Transaction "{transaction.transaction_uuid}" was updated successfully.')
            return redirect('admin_transaction_list')
        except Exception as e:
            messages.error(request, f'Error updating transaction: {str(e)}')
    
    status_choices = PaymentTransaction.STATUS_CHOICES
    context = {
        'transaction': transaction,
        'status_choices': status_choices,
        'is_edit': True,
    }
    return render(request, 'admin/transaction_form.html', context)

@login_required
@user_passes_test(is_admin)
def transaction_delete(request, transaction_id):
    """Delete transaction"""
    transaction = get_object_or_404(PaymentTransaction, id=transaction_id)
    
    if request.method == 'POST':
        transaction_uuid = transaction.transaction_uuid
        transaction.delete()
        messages.success(request, f'Transaction "{transaction_uuid}" was deleted successfully.')
        return redirect('admin_transaction_list')
    
    return render(request, 'admin/transaction_confirm_delete.html', {'transaction': transaction})

@login_required
@user_passes_test(is_admin)
def transaction_bulk_action(request):
    """Handle bulk actions for transactions"""
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_transactions')
        
        if not selected_ids:
            messages.error(request, 'No transactions selected.')
            return redirect('admin_transaction_list')
        
        transactions = PaymentTransaction.objects.filter(id__in=selected_ids)
        
        if action == 'delete':
            count = transactions.count()
            transactions.delete()
            messages.success(request, f'{count} transactions were deleted successfully.')
        
        elif action == 'update_status':
            new_status = request.POST.get('new_status')
            if new_status:
                transactions.update(status=new_status)
                messages.success(request, f'Status updated for {transactions.count()} transactions.')
    
    return redirect('admin_transaction_list')

@login_required
@user_passes_test(is_admin)
def quick_update_stock(request):
    """AJAX endpoint for quick stock updates"""
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        new_stock = data.get('new_stock')
        
        try:
            product = Product.objects.get(id=product_id)
            product.quantity_available = new_stock
            product.save()
            return JsonResponse({'success': True, 'message': 'Stock updated successfully'})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})