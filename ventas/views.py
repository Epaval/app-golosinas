from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.utils.timezone import make_aware
from django.contrib import messages
from django.db.models import Q, Sum, Count
from datetime import timedelta, datetime, time   
from .models import Producto, Cliente, Venta, DetalleVenta
from .forms import (
    ProductoForm, ClienteForm, VentaForm,
     LoginForm
)
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json
from utils.bcv import get_usd_rate


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
    hoy = timezone.localdate()
    primer_dia_mes = hoy.replace(day=1)

    # 🔧 Helper para filtrar por fecha local
    def get_rango_fecha(fecha):
        tz = timezone.get_current_timezone()
        inicio = timezone.make_aware(datetime.combine(fecha, time(0, 0)), tz)
        fin = inicio + timedelta(days=1)
        return inicio, fin

    inicio_hoy, fin_hoy = get_rango_fecha(hoy)
    inicio_mes, fin_mes = get_rango_fecha(primer_dia_mes)

    # Consultas seguras por rango
    ventas_hoy_qs = Venta.objects.filter(fecha__gte=inicio_hoy, fecha__lt=fin_hoy)
    ventas_hoy = ventas_hoy_qs.count()
    ingresos_hoy = ventas_hoy_qs.aggregate(total=Sum('total'))['total'] or 0

    ventas_mes_qs = Venta.objects.filter(fecha__gte=inicio_mes, fecha__lt=fin_mes + timedelta(days=1))
    ventas_mes = ventas_mes_qs.count()
    ingresos_mes = ventas_mes_qs.aggregate(total=Sum('total'))['total'] or 0

    productos_bajo_stock = Producto.objects.filter(activo=True, stock__lte=10).order_by('stock')[:10]

    # 🔍 BÚSQUEDA Y FILTROS PARA ÚLTIMAS VENTAS
    query = request.GET.get('q', '').strip()
    estado_filter = request.GET.get('estado', '')
    
    # QuerySet base para ventas recientes
    ultimas_ventas_qs = Venta.objects.select_related('cliente', 'usuario').prefetch_related('detalles__producto').order_by('-fecha')
    
    # Aplicar filtros de búsqueda
    if query:
        ultimas_ventas_qs = ultimas_ventas_qs.filter(
            Q(pk__icontains=query) |
            Q(cliente__nombre__icontains=query) |
            Q(cliente__apellido__icontains=query) |
            Q(cliente__telefono__icontains=query) |
            Q(notas__icontains=query)
        )
    
    if estado_filter and estado_filter in ['pendiente', 'parcial', 'pagado']:
        ultimas_ventas_qs = ultimas_ventas_qs.filter(estado_pago=estado_filter)

    # 📄 PAGINACIÓN
    paginator = Paginator(ultimas_ventas_qs, 10)
    page = request.GET.get('page')
    
    try:
        ultimas_ventas = paginator.page(page)
    except PageNotAnInteger:
        ultimas_ventas = paginator.page(1)
    except EmptyPage:
        ultimas_ventas = paginator.page(paginator.num_pages)

    # 📊 Gráfico últimos 7 días
    fechas, ventas_por_dia, ingresos_por_dia = [], [], []
    for i in range(6, -1, -1):
        fecha = hoy - timedelta(days=i)
        fechas.append(fecha.strftime('%d/%m'))
        ini, fin = get_rango_fecha(fecha)
        qs = Venta.objects.filter(fecha__gte=ini, fecha__lt=fin)
        ventas_por_dia.append(qs.count())
        ingresos_por_dia.append(float(qs.aggregate(total=Sum('total'))['total'] or 0))

    context = {
        'total_productos': Producto.objects.filter(activo=True).count(),
        'total_clientes': Cliente.objects.filter(activo=True).count(),
        'ventas_hoy': ventas_hoy,
        'ingresos_hoy': ingresos_hoy,
        'ventas_mes': ventas_mes,
        'ingresos_mes': ingresos_mes,
        'productos_bajo_stock': productos_bajo_stock,
        'ultimas_ventas': ultimas_ventas,
        'paginator': paginator,
        'page_obj': ultimas_ventas,
        'query': query,
        'estado_filter': estado_filter,
        'fechas_ultimos_7_dias': fechas,
        'ventas_ultimos_7_dias': ventas_por_dia,
        'ingresos_ultimos_7_dias': ingresos_por_dia,
    }

    return render(request, 'ventas/dashboard.html', context)


# ─── Productos ─────────────────────────────────────────────────────────────────

@login_required
def producto_lista(request):
    q = request.GET.get('q', '')
    productos = Producto.objects.filter(activo=True)
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    return render(request, 'ventas/producto_lista.html',
                  {'productos': productos, 'q': q})


@login_required
def producto_nuevo(request):
    form = ProductoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto creado correctamente.')
        return redirect('producto_lista')
    return render(request, 'ventas/producto_form.html',
                  {'form': form, 'titulo': 'Nuevo Producto'})


@login_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('producto_lista')
    return render(request, 'ventas/producto_form.html',
                  {'form': form, 'titulo': 'Editar Producto'})


@login_required
def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.activo = False
        producto.save()
        messages.success(request, 'Producto desactivado.')
        return redirect('producto_lista')
    return render(request, 'ventas/confirmar_eliminar.html',
                  {'objeto': producto, 'tipo': 'producto'})


# ─── Clientes ──────────────────────────────────────────────────────────────────

@login_required
def cliente_lista(request):
    q = request.GET.get('q', '')
    clientes = Cliente.objects.filter(activo=True)
    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) |
            Q(telefono__icontains=q))
    return render(request, 'ventas/cliente_lista.html',
                  {'clientes': clientes, 'q': q})


@login_required
def cliente_nuevo(request):
    form = ClienteForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cliente creado correctamente.')
        return redirect('cliente_lista')
    return render(request, 'ventas/cliente_form.html',
                  {'form': form, 'titulo': 'Nuevo Cliente'})


@login_required
def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cliente actualizado.')
        return redirect('cliente_lista')
    return render(request, 'ventas/cliente_form.html',
                  {'form': form, 'titulo': 'Editar Cliente'})


@login_required
def cliente_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.activo = False
        cliente.save()
        messages.success(request, 'Cliente desactivado.')
        return redirect('cliente_lista')
    return render(request, 'ventas/confirmar_eliminar.html',
                  {'objeto': cliente, 'tipo': 'cliente'})

@login_required
def resumen_cliente_ventas(request):
    """
    Vista para resumen de ventas por cliente con filtros de período y estado de pago
    """
    from decimal import Decimal
    from utils.bcv import get_usd_rate
    
    # Obtener parámetros de filtro
    cliente_id = request.GET.get('cliente', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    estado_pago = request.GET.get('estado_pago', '')
    
    # Query base
    ventas = Venta.objects.select_related('cliente', 'usuario').prefetch_related('detalles__producto')
    
    # Inicializar variables de fecha
    fecha_desde_obj = None
    fecha_hasta_obj = None
    
    # Aplicar filtro por cliente
    if cliente_id:
        ventas = ventas.filter(cliente_id=cliente_id)
    
    # Aplicar filtro por fecha
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
            fecha_desde_inicio = make_aware(datetime.combine(fecha_desde_obj, datetime.min.time()))
            ventas = ventas.filter(fecha__gte=fecha_desde_inicio)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            fecha_hasta_fin = make_aware(datetime.combine(fecha_hasta_obj, datetime.max.time()))
            ventas = ventas.filter(fecha__lte=fecha_hasta_fin)
        except ValueError:
            pass
    
    # Aplicar filtro por estado de pago
    if estado_pago in ['pendiente', 'pagado', 'parcial']:
        ventas = ventas.filter(estado_pago=estado_pago)
    
    # Obtener tasa BCV actual (para ventas sin tasa guardada)
    tasa_bcv_actual = get_usd_rate()
    
    # Ordenar por cliente y fecha
    ventas = ventas.order_by('cliente__nombre', '-fecha')
    
    # Agrupar ventas por cliente
    clientes_resumen = {}
    total_global_usd = 0
    total_global_bs = 0
    total_ventas_global = 0
    tasa_utilizada = tasa_bcv_actual
    
    for venta in ventas:
        cliente_nombre = venta.cliente.nombre_completo
        
        # Calcular total en bolívares si no está guardado
        if venta.total_bs:
            total_bs_venta = float(venta.total_bs)
        else:
            # Usar la tasa actual para calcular
            total_bs_venta = float(venta.total) * float(tasa_bcv_actual)
        
        if cliente_nombre not in clientes_resumen:
            clientes_resumen[cliente_nombre] = {
                'cliente_id': venta.cliente.id,
                'cliente': venta.cliente,
                'ventas': [],
                'total_usd': 0,
                'total_bs': 0,
                'cantidad_ventas': 0,
                'pendientes': 0,
                'parciales': 0,
                'pagados': 0,
            }
        
        # Agregar venta con el total_bs calculado
        venta_data = {
            'pk': venta.pk,
            'id': venta.pk,
            'fecha': venta.fecha,
            'total': venta.total,
            'total_bs': total_bs_venta,
            'estado_pago': venta.estado_pago,
            'estado_pago_display': venta.get_estado_pago_display(),
        }
        
        clientes_resumen[cliente_nombre]['ventas'].append(venta_data)
        clientes_resumen[cliente_nombre]['total_usd'] += float(venta.total)
        clientes_resumen[cliente_nombre]['total_bs'] += total_bs_venta
        clientes_resumen[cliente_nombre]['cantidad_ventas'] += 1
        
        # Contar por estado
        if venta.estado_pago == 'pendiente':
            clientes_resumen[cliente_nombre]['pendientes'] += 1
        elif venta.estado_pago == 'parcial':
            clientes_resumen[cliente_nombre]['parciales'] += 1
        elif venta.estado_pago == 'pagado':
            clientes_resumen[cliente_nombre]['pagados'] += 1
        
        total_global_usd += float(venta.total)
        total_global_bs += total_bs_venta
        total_ventas_global += 1
    
    clientes_lista = Cliente.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'resumen_clientes': clientes_resumen,
        'clientes_lista': clientes_lista,
        'cliente_seleccionado': cliente_id,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estado_pago_seleccionado': estado_pago,
        'fecha_desde_obj': fecha_desde_obj,
        'fecha_hasta_obj': fecha_hasta_obj,
        'total_global_usd': total_global_usd,
        'total_global_bs': total_global_bs,
        'total_ventas_global': total_ventas_global,
        'total_clientes_global': len(clientes_resumen),
        'tasa_bcv_actual': float(tasa_bcv_actual),
    }
    
    return render(request, 'ventas/resumen_cliente_ventas.html', context)
 



# ─── Ventas ────────────────────────────────────────────────────────────────────


def venta_lista(request):
    ventas = Venta.objects.select_related(
        'cliente', 'usuario'
    ).prefetch_related('detalles__producto').order_by('-fecha')

    estado_pago = request.GET.get('pago', '')
    if estado_pago in ['pendiente', 'parcial', 'pagado']:
        ventas = ventas.filter(estado_pago=estado_pago)

    return render(request, 'ventas/venta_lista.html', {'ventas': ventas})



def venta_nueva(request):
    form = VentaForm(request.POST or None)
    
    if request.method == 'POST':
        print("\n📥 POST keys:", list(request.POST.keys()))
        print("📦 Productos recibidos:", request.POST.getlist('producto_id[]'))
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    venta = form.save(commit=False)
                    venta.usuario = request.user
                    venta.fecha = timezone.now()
                    venta.estado = 'completada'
                    venta.estado_pago = 'pendiente'
                    venta.save()
                    
                    productos_ids = request.POST.getlist('producto_id[]')
                    cantidades = request.POST.getlist('cantidad[]')
                    
                    detalles_validos = 0
                    for i, pid in enumerate(productos_ids):
                        if not pid:
                            continue
                        try:
                            cantidad = int(cantidades[i])
                            producto = Producto.objects.get(pk=pid, activo=True)
                            
                            if cantidad <= 0 or cantidad > producto.stock:
                                continue
                            
                            DetalleVenta.objects.create(
                                venta=venta,
                                producto=producto,
                                cantidad=cantidad,
                                precio_unitario=producto.precio_unitario
                            )
                            
                            producto.stock = max(0, producto.stock - cantidad)
                            producto.save(update_fields=['stock'])
                            detalles_validos += 1
                        except (ValueError, Producto.DoesNotExist):
                            continue
                    
                    if detalles_validos == 0:
                        messages.error(request, '⚠️ Agrega al menos 1 producto válido.')
                        venta.delete()
                        return redirect('venta_nueva')
                    
                    venta.calcular_total()
                    messages.success(request, f'✅ Venta #{venta.pk} registrada por ${venta.total:.2f}.')
                    return redirect('venta_lista')
                    
            except Exception as e:
                print(f"❌ Error DB: {e}")
                messages.error(request, f'❌ Error interno: {e}')
        else:
            print(f"❌ Errores del form: {form.errors}")
            messages.error(request, f'❌ Revisa los datos: {form.errors.as_text()}')
    
    return render(request, 'ventas/venta_form.html', {
        'form': form,
        'productos': Producto.objects.filter(activo=True, stock__gt=0)
    })



def venta_detalle(request, pk):
    venta = get_object_or_404(
        Venta.objects.select_related('cliente', 'usuario'), pk=pk)
    detalles = venta.detalles.select_related('producto').all()
    return render(request, 'ventas/venta_detalle.html',
                  {'venta': venta, 'detalles': detalles})



def cliente_ventas_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk, activo=True)
    estado_pago = request.GET.get('estado_pago', '')
    ventas = cliente.ventas.select_related(
        'usuario').prefetch_related('detalles__producto')

    if estado_pago:
        ventas = ventas.filter(estado_pago=estado_pago)

    ventas = ventas.order_by('-fecha')

    total_ventas = sum(v.total for v in ventas if v.estado == 'completada')
    total_pendiente = sum(
        v.total for v in ventas
        if v.estado_pago == 'pendiente' and v.estado == 'completada')
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
    venta = get_object_or_404(Venta, pk=venta_pk)
    nuevo_estado = request.POST.get('estado')

    if nuevo_estado not in ['pendiente', 'parcial', 'pagado']:
        return JsonResponse(
            {'success': False, 'error': 'Estado inválido'}, status=400)

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


# ─── API BCV ───────────────────────────────────────────────────────────────────

@login_required
def api_bcv_rate(request):
    """Endpoint para obtener la tasa actual via AJAX"""
    try:
        rate = get_usd_rate()
        return JsonResponse({
            'usd_rate': float(rate),
            'success': True
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def venta_guardar_tasa(request, pk):
    """Guarda la tasa BCV en una venta y calcula el total en Bs"""
    try:
        venta = get_object_or_404(Venta, pk=pk)
        data = json.loads(request.body)
        tasa = Decimal(str(data.get('tasa')))
        
        venta.tasa_bcv = tasa
        venta.total_usd = venta.total
        venta.total_bs = venta.total * tasa
        venta.save(update_fields=['tasa_bcv', 'total_usd', 'total_bs'])
        
        return JsonResponse({
            'success': True,
            'total_bs': float(venta.total_bs),
            'tasa': float(tasa)
        })
    except Venta.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Venta no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
