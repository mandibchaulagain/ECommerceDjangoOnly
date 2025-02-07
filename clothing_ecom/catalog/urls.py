from django.urls import path
from .views import mensClothing
urlpatterns = [
    path('',mensClothing,name='mensClothing'),
]