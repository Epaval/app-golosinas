from django.contrib import admin
from .models import Producto, Cliente, Venta, DetalleVenta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    readonly_fields = ['subtotal']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio_unitario', 'stock', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'telefono', 'email', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'apellido', 'telefono']


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['pk', 'cliente', 'usuario', 'fecha', 'estado', 'total']
    list_filter = ['estado', 'fecha']
    inlines = [DetalleVentaInline]
    readonly_fields = ['total', 'fecha']


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ['venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    readonly_fields = ['subtotal']
