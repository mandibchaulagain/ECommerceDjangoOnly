from django.urls import path
from .views import home,thankyoupage

urlpatterns = [
    path('', home, name='home'),
    path('thankyou/',thankyoupage, name="thankyou")
]