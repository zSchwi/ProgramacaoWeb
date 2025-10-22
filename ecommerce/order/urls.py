from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('create-from-cart/<int:cart_id>/', views.create_from_cart, name='order_create_from_cart'),
]
