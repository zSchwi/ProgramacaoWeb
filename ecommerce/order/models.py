from decimal import Decimal
from django.conf import settings
from django.db import models, transaction

class Order(models.Model):
    """
    Order que guarda os itens em JSONField (cada item: product_id, name, price, quantity, subtotal).
    Pode ser criado/populado a partir de um Cart existente.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_PAID = 'PAID'
    STATUS_SHIPPED = 'SHIPPED'
    ORDER_STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_PAID, 'Pago'),
        (STATUS_SHIPPED, 'Enviado'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', verbose_name='Usuário')
    items = models.JSONField(default=list, blank=True, verbose_name='Itens')  # lista de dicts com detalhes dos itens
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='Total')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Status')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    cart = models.ForeignKey('cart.Cart', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name='Carrinho')

    def __str__(self):
        return f"Pedido #{self.id} - {self.user} - {self.get_status_display()}"

    @transaction.atomic
    def populate_from_cart(self, cart):
        """
        Preenche self.items a partir do cart (substitui itens atuais), recalcula total e salva.
        Os campos price/subtotal são serializados como strings para compatibilidade JSON.
        """
        # elimina itens antigos
        self.items = []
        total = Decimal('0.00')
        for cart_item in cart.items.select_related('product').all():
            product = cart_item.product
            price = getattr(product, 'price', Decimal('0.00')) or Decimal('0.00')
            quantity = int(cart_item.quantity or 0)
            subtotal = price * quantity
            # armazena dados essenciais (price/subtotal como string para JSON seguro)
            item_data = {
                'product_id': product.id if product else None,
                'name': getattr(product, 'name', str(product)),
                'price': str(price),
                'quantity': quantity,
                'subtotal': str(subtotal),
            }
            self.items.append(item_data)
            total += subtotal
        self.total = total
        self.cart = cart
        self.save()
        return self

    @classmethod
    @transaction.atomic
    def create_from_cart(cls, cart, user=None, status=STATUS_PENDING):
        """
        Cria um Order a partir do cart e retorna a instância criada.
        """
        if user is None:
            user = getattr(cart, 'user', None)
        order = cls.objects.create(user=user, total=Decimal('0.00'), status=status, cart=cart, items=[])
        order.populate_from_cart(cart)
        return order

    def get_items(self):
        """
        Retorna a lista de itens desserializada (com price e subtotal como Decimal).
        """
        result = []
        for it in self.items or []:
            price = Decimal(it.get('price', '0')) if it.get('price') is not None else Decimal('0')
            subtotal = Decimal(it.get('subtotal', '0')) if it.get('subtotal') is not None else price * int(it.get('quantity', 0))
            result.append({
                'product_id': it.get('product_id'),
                'name': it.get('name'),
                'price': price,
                'quantity': int(it.get('quantity', 0)),
                'subtotal': subtotal,
            })
        return result

    def get_total(self):
        return self.total

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
