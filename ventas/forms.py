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


# ventas/forms.py
from django import forms
from .models import Producto, Cliente, Venta

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio_unitario', 'stock', 'imagen', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
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
        fields = ['cliente', 'notas']  # ✅ Quitar 'estado' de aquí
        widgets = {
            'cliente': forms.Select(attrs={'class': CSS_SELECT}),
            'notas': forms.Textarea(attrs={'class': CSS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notas'].required = False