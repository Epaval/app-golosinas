from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from ventas import views as ventas_views

# Importación necesaria para RedirectView
from django.views.generic import RedirectView

urlpatterns = [
    # PWA redirecciones
    path('manifest.json', RedirectView.as_view(url='/static/manifest.json', permanent=True)),
    path('sw.js', RedirectView.as_view(url='/static/sw.js', permanent=True)),
    
    # Página principal - pública (ventas)
    path('', ventas_views.venta_nueva, name='home'),
    
    # URLs de administración (protegidas por login)
    path('admin-panel/', include('ventas.urls')),
    
    # Django admin
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
