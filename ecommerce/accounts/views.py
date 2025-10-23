from django.contrib.auth.views import LoginView
from .forms import CustomLoginForm
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, logout


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'  # caminho do template
    authentication_form = CustomLoginForm

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('product_list')  # redireciona após login


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
        return redirect('product_list')

    return render(request, 'accounts/register.html')

def logout_view(request):
        logout(request)
        messages.success(request, "Você saiu da sua conta.")
        return redirect('product_list')