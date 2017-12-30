from django import forms
from .models import Order

class OrderFormForBuyer(forms.ModelForm):
    product_name = forms.TextInput()

    def __init__(self, *args, **kwargs):
         super(OrderFormForBuyer, self).__init__(*args, **kwargs)

    class Meta:
        model = Order
        fields = ('id', 'quantity')
