from django.contrib import admin
from django.utils.html import format_html
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total', 'status', 'created_at', 'cart')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'id')
    fields = ('user', 'cart', 'items_display', 'total', 'status', 'created_at')
    readonly_fields = ('created_at', 'total', 'items_display')

    def items_display(self, obj):
        """
        Retorna uma representação legível dos itens: quantidade x nome = valor do produto (unitário).
        """
        lines = []
        for it in obj.get_items():
            lines.append(f"{it['quantity']}x {it['name']} = {it['price']}")
        if not lines:
            return "(sem itens)"
        return format_html('<br/>'.join(lines))
    items_display.short_description = "Itens"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cart = form.cleaned_data.get('cart')
        if cart:
            obj.populate_from_cart(cart)
        else:
            total = sum(it['subtotal'] for it in obj.get_items())
            if obj.total != total:
                obj.total = total
                obj.save()
