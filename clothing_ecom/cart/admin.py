from django.contrib import admin
from .models import PaymentTransaction

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_uuid', 'product_code', 'total_amount', 'status', 'ref_id', 'created_at')
    search_fields = ('transaction_uuid', 'product_code', 'status')
    list_filter = ('status', 'created_at')