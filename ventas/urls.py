from django.urls import path
from . import views

urlpatterns = [
    # Auth (solo para administradores)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard (solo administradores)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Productos
    path('productos/', views.producto_lista, name='producto_lista'),
    path('productos/nuevo/', views.producto_nuevo, name='producto_nuevo'),
    path('productos/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('productos/<int:pk>/eliminar/', views.producto_eliminar, name='producto_eliminar'),
    
    # Clientes
    path('clientes/', views.cliente_lista, name='cliente_lista'),
    path('clientes/nuevo/', views.cliente_nuevo, name='cliente_nuevo'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/eliminar/', views.cliente_eliminar, name='cliente_eliminar'),
    path('clientes/<int:pk>/ventas/', views.cliente_ventas_detalle, name='cliente_ventas_detalle'),
    
    # Ventas (gestión)
    path('nueva/', views.venta_nueva, name='venta_nueva'),
    path('ventas/', views.venta_lista, name='venta_lista'),
    path('ventas/<int:pk>/', views.venta_detalle, name='venta_detalle'),
    path('ventas/<int:venta_pk>/cambiar-pago-ajax/', views.venta_cambiar_pago_ajax, name='venta_cambiar_pago_ajax'),
    
    # Resumen y reportes
    path('resumen-cliente-ventas/', views.resumen_cliente_ventas, name='resumen_cliente_ventas'),
    
    # API
    path('api/bcv-rate/', views.api_bcv_rate, name='api_bcv_rate'),
    path('api/venta/<int:pk>/guardar-tasa/', views.venta_guardar_tasa, name='venta_guardar_tasa'),
]
