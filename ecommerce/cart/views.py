from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from store.models import Product
from .models import Cart, CartItem
from order.models import Order 
from decimal import Decimal 
from django.http import HttpResponse  
from django.contrib import messages  
from django.urls import reverse 


def _merge_session_cart(request, user):
    """
    Move itens do carrinho em sessão para o Cart vinculado ao usuário.
    Usar antes de exibir ou finalizar checkout para garantir que o Cart do usuário contenha os itens.
    """
    session_cart = request.session.get('cart', {}) or {}
    if not session_cart:
        return
    cart, created = Cart.objects.get_or_create(user=user)
    for pid_str, qty in session_cart.items():
        try:
            pid = int(pid_str)
            product = Product.objects.get(pk=pid)
        except (ValueError, Product.DoesNotExist):
            continue
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity = cart_item.quantity + int(qty) if not created else int(qty)
        cart_item.save()
    # limpa carrinho de sessão
    request.session['cart'] = {}
    request.session.modified = True


@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    total = cart.total()
    return render(request, 'cart/cart_detail.html', {'cart': cart, 'items': items, 'total': total})


@login_required
def add_to_cart(request, product_id):
    """
    Adiciona produto ao carrinho do usuário autenticado.
    Se não autenticado, mostra mensagem e redireciona para login com next.
    """
    product = get_object_or_404(Product, id=product_id)

    if not request.user.is_authenticated:
        messages.error(request, "Você precisa entrar para adicionar produtos ao carrinho.")
        login_url = reverse('login')
        # tenta enviar de volta para o detalhe do produto (se existir), senão refere para home
        referer = request.META.get('HTTP_REFERER')
        next_url = referer or reverse('product_detail', args=[product_id]) if product_id else reverse('product_list')
        return redirect(f"{login_url}?next={next_url}")

    # se estiver logado, usa o Cart vinculado ao usuário
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    messages.success(request, f"{product.name} adicionado ao carrinho.")
    return redirect('cart_detail')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_detail')

# 🔹 4. Atualizar quantidade de um item
@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart_item.quantity = max(1, quantity)  # impede quantidade 0
        cart_item.save()
    return redirect('cart_detail')

@login_required
def checkout(request):
    """
    GET: mostra página de confirmação antes de finalizar a compra.
    POST: cria Order a partir do Cart do usuário autenticado, esvazia o carrinho e mostra confirmação.
    """
    # mescla o carrinho de sessão para o Cart do usuário (se houver)
    try:
        _merge_session_cart(request, request.user)
    except Exception:
        pass

    cart, created = Cart.objects.get_or_create(user=request.user)

    # se GET -> mostrar confirmação (dentro do layout)
    if request.method == 'GET':
        items = cart.items.select_related('product').all()
        total = cart.total()
        return render(request, 'cart/checkout_confirm.html', {'cart': cart, 'items': items, 'total': total})

    # se POST -> tenta finalizar
    if request.method == 'POST':
        # após merge, verifica novamente se há itens
        cart.refresh_from_db()
        if not cart.items.exists():
            messages.error(request, "Seu carrinho está vazio.")
            return redirect('cart_detail')

        # cria o pedido a partir do cart vinculado ao usuário
        order = Order.create_from_cart(cart, user=request.user)

        # esvazia o carrinho (remove os CartItem)
        cart.items.all().delete()

        messages.success(request, f"Compra finalizada com sucesso. Pedido #{order.id} criado.")
        return render(request, 'cart/checkout_success.html', {'order': order})

    # fallback
    return redirect('cart_detail')
