from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Sum, Count
from datetime import timedelta, datetime
from .models import Producto, Cliente, Venta, DetalleVenta
from .forms import (
    ProductoForm, ClienteForm, VentaForm,
    DetalleVentaFormSet, LoginForm
)


# ─── Autenticación ─────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'ventas/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Dashboard ─────────────────────────────────────────────────────────────────
@login_required  
def dashboard(request):
    # Obtener fecha actual
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    # ========== DATOS PARA LAS TARJETAS ==========
    total_productos = Producto.objects.filter(activo=True).count()
    total_clientes = Cliente.objects.filter(activo=True).count()
    
    # 🔥 CORRECCIÓN: Usar rango de fechas con zona horaria
    # Crear inicio y fin del día en la zona horaria local
    inicio_dia = timezone.make_aware(datetime.combine(hoy, datetime.min.time()))
    fin_dia = timezone.make_aware(datetime.combine(hoy, datetime.max.time()))
    
    # Ventas de hoy usando rango
    ventas_hoy = Venta.objects.filter(fecha__range=(inicio_dia, fin_dia)).count()
    ingresos_hoy = Venta.objects.filter(fecha__range=(inicio_dia, fin_dia)).aggregate(total=Sum('total'))['total'] or 0
    
    # Ventas del mes (usando fecha__date para simplificar)
    ventas_mes = Venta.objects.filter(fecha__date__gte=primer_dia_mes).count()
    ingresos_mes = Venta.objects.filter(fecha__date__gte=primer_dia_mes).aggregate(total=Sum('total'))['total'] or 0
    
    # ========== PRODUCTOS CON BAJO STOCK ==========
    productos_bajo_stock = Producto.objects.filter(activo=True, stock__lte=10).order_by('stock')[:10]
    
    # ========== ÚLTIMAS 10 VENTAS ==========
    ultimas_ventas = Venta.objects.select_related('cliente').all().order_by('-fecha')[:10]
    
    # ========== DATOS PARA EL GRÁFICO (ÚLTIMOS 7 DÍAS) ==========
    fechas = []
    ventas_por_dia = []
    ingresos_por_dia = []
    
    for i in range(6, -1, -1):
        fecha = hoy - timedelta(days=i)
        fechas.append(fecha.strftime('%d/%m'))
        
        # Usar rango para cada día
        inicio = timezone.make_aware(datetime.combine(fecha, datetime.min.time()))
        fin = timezone.make_aware(datetime.combine(fecha, datetime.max.time()))
        
        ventas_dia = Venta.objects.filter(fecha__range=(inicio, fin)).count()
        ingresos_dia = Venta.objects.filter(fecha__range=(inicio, fin)).aggregate(total=Sum('total'))['total'] or 0
        
        ventas_por_dia.append(ventas_dia)
        ingresos_por_dia.append(float(ingresos_dia))
    
    # Debug para verificar
    print(f"=== DASHBOARD DEBUG ===")
    print(f"Fecha actual: {hoy}")
    print(f"Inicio día: {inicio_dia}")
    print(f"Fin día: {fin_dia}")
    print(f"Ventas hoy: {ventas_hoy}")
    print(f"Ingresos hoy: {ingresos_hoy}")
    print(f"Ventas mes: {ventas_mes}")
    print(f"Ingresos mes: {ingresos_mes}")
    print(f"Total ventas en DB: {Venta.objects.count()}")
    
    context = {
        'total_productos': total_productos,
        'total_clientes': total_clientes,
        'ventas_hoy': ventas_hoy,
        'ingresos_hoy': ingresos_hoy,
        'ventas_mes': ventas_mes,
        'ingresos_mes': ingresos_mes,
        'productos_bajo_stock': productos_bajo_stock,
        'ultimas_ventas': ultimas_ventas,
        'fechas_ultimos_7_dias': fechas,
        'ventas_ultimos_7_dias': ventas_por_dia,
        'ingresos_ultimos_7_dias': ingresos_por_dia,
    }
    
    return render(request, 'ventas/dashboard.html', context)


# ─── Productos ─────────────────────────────────────────────────────────────────

@login_required
def producto_lista(request):
    q = request.GET.get('q', '')
    productos = Producto.objects.all()
    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    return render(request, 'ventas/producto_lista.html', {'productos': productos, 'q': q})


@login_required
def producto_nuevo(request):
    form = ProductoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto creado correctamente.')
        return redirect('producto_lista')
    return render(request, 'ventas/producto_form.html', {'form': form, 'titulo': 'Nuevo Producto'})


@login_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=producto)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('producto_lista')
    return render(request, 'ventas/producto_form.html', {'form': form, 'titulo': 'Editar Producto'})


@login_required
def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.activo = False
        producto.save()
        messages.success(request, 'Producto desactivado.')
        return redirect('producto_lista')
    return render(request, 'ventas/confirmar_eliminar.html', {'objeto': producto, 'tipo': 'producto'})


# ─── Clientes ──────────────────────────────────────────────────────────────────

@login_required
def cliente_lista(request):
    q = request.GET.get('q', '')
    clientes = Cliente.objects.filter(activo=True)
    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(telefono__icontains=q)
        )
    return render(request, 'ventas/cliente_lista.html', {'clientes': clientes, 'q': q})


@login_required
def cliente_nuevo(request):
    form = ClienteForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cliente creado correctamente.')
        return redirect('cliente_lista')
    return render(request, 'ventas/cliente_form.html', {'form': form, 'titulo': 'Nuevo Cliente'})


@login_required
def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cliente actualizado.')
        return redirect('cliente_lista')
    return render(request, 'ventas/cliente_form.html', {'form': form, 'titulo': 'Editar Cliente'})


@login_required
def cliente_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.activo = False
        cliente.save()
        messages.success(request, 'Cliente desactivado.')
        return redirect('cliente_lista')
    return render(request, 'ventas/confirmar_eliminar.html', {'objeto': cliente, 'tipo': 'cliente'})


# ─── Ventas ────────────────────────────────────────────────────────────────────

@login_required
def venta_lista(request):
    ventas = Venta.objects.select_related('cliente', 'usuario').prefetch_related('detalles__producto').order_by('-fecha')
    
    # 🔍 Filtro por estado de pago
    estado_pago = request.GET.get('pago', '')
    if estado_pago in ['pendiente', 'parcial', 'pagado']:
        ventas = ventas.filter(estado_pago=estado_pago)
        
    return render(request, 'ventas/venta_lista.html', {'ventas': ventas})


@login_required
def venta_nueva(request):
    form = VentaForm(request.POST or None)
    formset = DetalleVentaFormSet(request.POST or None, prefix='detalles')
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        venta = form.save(commit=False)
        venta.usuario = request.user
        venta.save()
        for detalle_form in formset:
            if detalle_form.cleaned_data and not detalle_form.cleaned_data.get('DELETE'):
                detalle = detalle_form.save(commit=False)
                detalle.venta = venta
                detalle.precio_unitario = detalle.producto.precio_unitario
                detalle.save()
                # Actualizar stock
                prod = detalle.producto
                prod.stock = max(0, prod.stock - detalle.cantidad)
                prod.save()
        venta.calcular_total()
        messages.success(request, f'Venta #{venta.pk} registrada por ${venta.total}.')
        return redirect('venta_lista')
    productos = Producto.objects.filter(activo=True, stock__gt=0)
    return render(request, 'ventas/venta_form.html', {
        'form': form, 'formset': formset, 'productos': productos
    })


@login_required
def venta_detalle(request, pk):
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'usuario'), pk=pk)
    detalles = venta.detalles.select_related('producto').all()
    return render(request, 'ventas/venta_detalle.html', {'venta': venta, 'detalles': detalles})


@login_required
def cliente_ventas_detalle(request, pk):
    """Muestra el historial de ventas de un cliente con estado de pago"""
    cliente = get_object_or_404(Cliente, pk=pk, activo=True)
    
    # Filtros opcionales
    estado_pago = request.GET.get('estado_pago', '')
    ventas = cliente.ventas.select_related('usuario').prefetch_related('detalles__producto')
    
    if estado_pago:
        ventas = ventas.filter(estado_pago=estado_pago)
    
    # Orden: más recientes primero
    ventas = ventas.order_by('-fecha')
    
    # Cálculo de totales
    total_ventas = sum(v.total for v in ventas if v.estado == 'completada')
    total_pendiente = sum(v.total for v in ventas if v.estado_pago == 'pendiente' and v.estado == 'completada')
    total_pagado = total_ventas - total_pendiente
    
    context = {
        'cliente': cliente,
        'ventas': ventas,
        'estado_pago_filter': estado_pago,
        'total_ventas': total_ventas,
        'total_pendiente': total_pendiente,
        'total_pagado': total_pagado,
    }
    return render(request, 'ventas/cliente_ventas_detalle.html', context)


@login_required
@require_POST
def venta_cambiar_pago_ajax(request, venta_pk):
    """Actualiza estado de pago vía AJAX y devuelve JSON"""
    venta = get_object_or_404(Venta, pk=venta_pk)
    nuevo_estado = request.POST.get('estado')
    
    if nuevo_estado not in ['pendiente', 'parcial', 'pagado']:
        return JsonResponse({'success': False, 'error': 'Estado inválido'}, status=400)
    
    venta.estado_pago = nuevo_estado
    if nuevo_estado == 'pagado' and not venta.fecha_pago:
        venta.fecha_pago = timezone.now()
    elif nuevo_estado != 'pagado':
        venta.fecha_pago = None
    venta.save(update_fields=['estado_pago', 'fecha_pago'])
    
    labels = {'pendiente': 'Pendiente', 'parcial': 'Parcial', 'pagado': 'Pagado'}
    return JsonResponse({
        'success': True,
        'estado': nuevo_estado,
        'label': labels[nuevo_estado],
        'venta_id': venta.pk
    })