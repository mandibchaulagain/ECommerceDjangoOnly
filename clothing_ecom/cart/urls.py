from django.urls import path
from . import views

urlpatterns = [
    path("", views.view_cart, name="view_cart"),  # View cart page
    path("add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),    
    path("remove/<int:cart_item_id>/<int:product_id>/<int:quantity>/", views.remove_from_cart, name="remove_from_cart"),#functionality not yet added
    path("buy/<int:product_id>/", views.buy,name="buy"),
    path("checkout/", views.checkout, name="checkout"),
    path("increase/<int:cart_item_id>/<int:product_id>/", views.increase_quantity, name="increase_quantity"),
    path("decrease/<int:cart_item_id>/<int:product_id>/", views.decrease_quantity, name="decrease_quantity"),
    path('payment/success/', views.success_payment, name='payment_success'),    
    path('payment/failure/', views.failure_payment, name='payment_failure'),
    

    # path("update/<int:cart_item_id>/", views.update_cart, name="update_cart"),  # Update quantity
]
