import os
from decimal import Decimal
from random import randint, choice

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from faker import Faker

# 🔽 REEMPLAZA 'mi_app' POR EL NOMBRE REAL DE TU APP
from ventas.models import Producto, Cliente, Venta, DetalleVenta


class Command(BaseCommand):
    help = 'Inserta 15 productos, 20 clientes y 5 ventas de prueba'

    def handle(self, *args, **kwargs):
        fake = Faker('es_ES')
        self.stdout.write(self.style.SUCCESS('🌱 Generando datos de prueba...'))

        with transaction.atomic():
            # 📦 1. PRODUCTOS (15)
            productos = []
            for _ in range(15):
                precio = Decimal(f"{randint(5, 300)}.{randint(0, 99):02d}")
                productos.append(Producto(
                    nombre=f"{fake.word().capitalize()} {fake.word().capitalize()}",
                    descripcion=fake.sentence(nb_words=8),
                    precio_unitario=precio,
                    stock=randint(0, 100),
                    activo=True
                ))
            Producto.objects.bulk_create(productos)
            self.stdout.write(self.style.SUCCESS('✅ 15 productos creados.'))

            # 👤 2. CLIENTES (20)
            clientes = []
            for _ in range(20):
                clientes.append(Cliente(
                    nombre=fake.first_name(),
                    apellido=fake.last_name(),
                    telefono=fake.phone_number(),
                    email=fake.email(),
                    direccion=fake.address(),
                    activo=True
                ))
            Cliente.objects.bulk_create(clientes)
            self.stdout.write(self.style.SUCCESS('✅ 20 clientes creados.'))

            # 🛒 3. VENTAS Y DETALLES (Opcional, pero recomendado para probar FK)
            # Necesitamos un usuario para registrar la venta
            usuario = User.objects.first()
            if not usuario:
                User.objects.create_superuser('admin_test', 'admin@test.com', 'admin123')
                usuario = User.objects.first()

            ventas_objs = []
            detalles_objs = []

            for _ in range(5):
                cliente = choice(Cliente.objects.all())
                ventas_objs.append(Venta(
                    cliente=cliente,
                    usuario=usuario,
                    estado='completada',
                    total=Decimal('0.00'),  # Se recalcula después
                    notas=fake.sentence()
                ))

            Venta.objects.bulk_create(ventas_objs)
            self.stdout.write(self.style.SUCCESS('✅ 5 ventas creadas.'))

            # Crear detalles para cada venta
            ventas_db = Venta.objects.all()[:5]
            for venta in ventas_db:
                num_items = randint(1, 3)
                for _ in range(num_items):
                    prod = choice(Producto.objects.all())
                    cant = randint(1, 5)
                    subtotal = cant * prod.precio_unitario
                    detalles_objs.append(DetalleVenta(
                        venta=venta,
                        producto=prod,
                        cantidad=cant,
                        precio_unitario=prod.precio_unitario,
                        subtotal=subtotal  # Calculado manualmente porque bulk_create ignora save()
                    ))

            DetalleVenta.objects.bulk_create(detalles_objs)

            # Recalcular totales reales de las ventas
            for venta in ventas_db:
                venta.calcular_total()

        self.stdout.write(self.style.SUCCESS('🎉 ¡Datos de prueba insertados correctamente!'))