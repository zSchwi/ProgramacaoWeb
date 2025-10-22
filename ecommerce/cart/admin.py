from django.contrib import admin
from .models import Cart, CartItem

admin.site.site_header = "Administração do Ecommerce"
admin.site.site_title = "Ecommerce"
admin.site.index_title = "Painel de Administração"

admin.site.register(Cart)
admin.site.register(CartItem)
