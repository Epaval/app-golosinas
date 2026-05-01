# 🍬 Golosinas — Sistema de Ventas

Sistema web con Django y MySQL para gestionar productos, clientes y ventas de un pequeño negocio de golosinas.

---

## ⚙️ Requisitos

- Python 3.10+
- MySQL 8.0+
- pip

---

## 🚀 Instalación paso a paso

### 1. Crear la base de datos en MySQL

```bash
mysql -u root -p < crear_bd.sql
```

### 2. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 3. Configurar la conexión a MySQL

Edita `golosinas/settings.py` y actualiza:

```python
DATABASES = {
    'default': {
        'NAME': 'golosinas_db',
        'USER': 'root',          # tu usuario
        'PASSWORD': 'tu_password', # tu contraseña
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 4. Crear tablas

```bash
python manage.py migrate
```

### 5. Crear superusuario (para login)

```bash
python manage.py createsuperuser
```

### 6. Iniciar el servidor

```bash
python manage.py runserver
```

Visita: **http://127.0.0.1:8000**

---

## 📱 Páginas principales

| URL | Descripción |
|-----|-------------|
| `/` | Dashboard con estadísticas |
| `/login/` | Inicio de sesión |
| `/productos/` | Lista de productos |
| `/clientes/` | Lista de clientes |
| `/ventas/` | Historial de ventas |
| `/ventas/nueva/` | Registrar nueva venta |
| `/admin/` | Panel de administración Django |

---

## 🗃️ Estructura de tablas

- **ventas_producto** — Catálogo de golosinas (nombre, precio, stock)
- **ventas_cliente** — Datos de clientes
- **ventas_venta** — Encabezado de cada venta (cliente, fecha, estado, total)
- **ventas_detalleventa** — Líneas de cada venta (producto, cantidad, subtotal)

---

## 🔒 Login

El sistema requiere autenticación. Usa el usuario creado con `createsuperuser`
o crea usuarios adicionales desde `/admin/`.
