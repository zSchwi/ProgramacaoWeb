from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Order
from cart.models import Cart

@login_required
def order_list(request):
    if request.user.is_staff:
        orders = Order.objects.all().order_by('-created_at')
    else:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if not (request.user.is_staff or order.user == request.user):
        return redirect('order_list')
    return render(request, 'order/order_detail.html', {'order': order})

@login_required
def create_from_cart(request, cart_id):
    cart = get_object_or_404(Cart, pk=cart_id)
    if not (request.user.is_staff or cart.user == request.user):
        return redirect('cart_detail')
    order = Order.create_from_cart(cart, user=cart.user)
    return redirect('order_detail', order_id=order.id)
