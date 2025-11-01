from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from django.contrib import messages
from django.urls import reverse

def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    # se não estiver logado, informa e redireciona para login (com next para voltar ao detalhe do produto)
    if not request.user.is_authenticated:
        messages.error(request, "Você precisa entrar para adicionar produtos ao carrinho.")
        login_url = reverse('login')
        next_url = reverse('product_detail', args=[product_id])
        return redirect(f"{login_url}?next={next_url}")

    # se estiver logado, delega para a view do app cart (persistência no modelo Cart)
    return redirect('add_to_cart', product_id=product_id)

def cart_detail(request):
    # se usuário autenticado, usa o app cart (Cart vinculado ao usuário)
    if request.user.is_authenticated:
        return redirect('cart_detail')

    cart = request.session.get('cart', {})
    product_ids = [int(pid) for pid in cart.keys()] if cart else []
    products = Product.objects.filter(id__in=product_ids) if product_ids else []
    items = [{'product': p, 'quantity': cart.get(str(p.id), 0)} for p in products]
    return render(request, 'store/cart.html', {'items': items})