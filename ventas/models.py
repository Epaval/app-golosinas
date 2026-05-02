from django.db import models
from django.contrib.auth.models import User


# ventas/models.py
from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario ($)")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True, verbose_name="Imagen")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - ${self.precio_unitario}"

class Cliente(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    apellido = models.CharField(max_length=150, blank=True, verbose_name="Apellido")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido}".strip()

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}".strip()


class Venta(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    ESTADO_PAGO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('parcial', 'Pago Parcial'),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT,
        related_name='ventas', verbose_name="Cliente"
    )
    usuario = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='ventas', verbose_name="Registrado por"
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    estado = models.CharField(
        max_length=15, choices=ESTADO_CHOICES,
        default='completada', verbose_name="Estado"
    )
    total = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=0, verbose_name="Total ($)"
    )
    notas = models.TextField(blank=True, verbose_name="Notas")

    estado_pago = models.CharField(
        max_length=15, choices=ESTADO_PAGO_CHOICES,
        default='pendiente',
        verbose_name="Estado de Pago"
    )

    fecha_pago = models.DateTimeField(
        blank=True, null=True, 
        verbose_name="Fecha de Pago"
    )

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta #{self.pk} - {self.cliente} - ${self.total}"

    def calcular_total(self):
        total = sum(d.subtotal for d in self.detalles.all())
        self.total = total
        self.save(update_fields=['total'])
        return total


class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta, on_delete=models.CASCADE,
        related_name='detalles', verbose_name="Venta"
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT,
        related_name='detalles', verbose_name="Producto"
    )
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Precio Unitario ($)"
    )
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=0, verbose_name="Subtotal ($)"
    )

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad} = ${self.subtotal}"
