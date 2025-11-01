from django.contrib.auth.views import LoginView
from .forms import CustomLoginForm
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from cart.models import Cart, CartItem
from store.models import Product


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'  
    authentication_form = CustomLoginForm

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy('product_list') 

    def form_valid(self, form):
        """
        Define a expiração da sessão de acordo com 'remember_me' antes de finalizar o login.
        Mescla o carrinho de sessão para o Cart do usuário, se existir.
        """
        remember = form.cleaned_data.get('remember_me')
        if remember:
            self.request.session.set_expiry(None)  
        else:
            self.request.session.set_expiry(0)

        response = super().form_valid(form)

        try:
            _merge_session_cart(self.request, self.request.user)
        except Exception:
            pass

        return response


# função utilitária para migrar itens da sessão para o Cart do usuário
def _merge_session_cart(request, user):
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
    request.session['cart'] = {}
    request.session.modified = True


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # validações básicas
        if password1 != password2:
            messages.error(request, "As senhas não coincidem.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Esse nome de usuário já está em uso.")
            return redirect('register')

        # cria o usuário
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        messages.success(request, "Conta criada com sucesso!")
        login(request, user)  # loga automaticamente
        # mantém o usuário logado por padrão após registro
        request.session.set_expiry(None)

        try:
            _merge_session_cart(request, user)
        except Exception:
            pass

        return redirect('product_list')

    return render(request, 'accounts/register.html')

def logout_view(request):
        logout(request)
        messages.success(request, "Você saiu da sua conta.")
        return redirect('product_list')