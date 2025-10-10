from django.urls import path
from . import admin_views

urlpatterns = [
    # Dashboard
    path('padmin/', admin_views.admin_dashboard, name='admin_dashboard'),
    
    # Product management
    path('padmin/products/', admin_views.product_list, name='admin_product_list'),
    path('padmin/products/add/', admin_views.product_add, name='admin_product_add'),
    path('padmin/products/<int:product_id>/edit/', admin_views.product_edit, name='admin_product_edit'),
    path('padmin/products/<int:product_id>/delete/', admin_views.product_delete, name='admin_product_delete'),
    path('padmin/products/bulk-action/', admin_views.product_bulk_action, name='admin_product_bulk_action'),
    
    # Transaction management
    path('padmin/transactions/', admin_views.transaction_list, name='admin_transaction_list'),
    path('padmin/transactions/add/', admin_views.transaction_add, name='admin_transaction_add'),
    path('padmin/transactions/<int:transaction_id>/edit/', admin_views.transaction_edit, name='admin_transaction_edit'),
    path('padmin/transactions/<int:transaction_id>/delete/', admin_views.transaction_delete, name='admin_transaction_delete'),
    path('padmin/transactions/bulk-action/', admin_views.transaction_bulk_action, name='admin_transaction_bulk_action'),
    
    # AJAX endpoints
    path('padmin/api/quick-update-stock/', admin_views.quick_update_stock, name='admin_quick_update_stock'),
]