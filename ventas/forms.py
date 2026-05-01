from django import forms
from django.forms import inlineformset_factory
from .models import Producto, Cliente, Venta, DetalleVenta


CSS = 'form-control'
CSS_SELECT = 'form-select'


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={'class': CSS, 'placeholder': 'Nombre de usuario'})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': CSS, 'placeholder': 'Contraseña'})
    )


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio_unitario', 'stock', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': CSS}),
            'descripcion': forms.Textarea(attrs={'class': CSS, 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': CSS, 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': CSS}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'telefono', 'email', 'direccion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': CSS}),
            'apellido': forms.TextInput(attrs={'class': CSS}),
            'telefono': forms.TextInput(attrs={'class': CSS}),
            'email': forms.EmailInput(attrs={'class': CSS}),
            'direccion': forms.Textarea(attrs={'class': CSS, 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'estado', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': CSS_SELECT}),
            'estado': forms.Select(attrs={'class': CSS_SELECT}),
            'notas': forms.Textarea(attrs={'class': CSS, 'rows': 2}),
        }


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad']
        widgets = {
            'producto': forms.Select(attrs={'class': CSS_SELECT + ' producto-select'}),
            'cantidad': forms.NumberInput(attrs={'class': CSS + ' cantidad-input', 'min': 1}),
        }


DetalleVentaFormSet = inlineformset_factory(
    Venta,
    DetalleVenta,
    form=DetalleVentaForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
