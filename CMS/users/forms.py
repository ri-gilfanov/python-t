from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from shop.models import LegalEntity
from django.utils import timezone
from django.forms import inlineformset_factory


class SignUpForm(UserCreationForm):
    class Meta:
        fields = ['first_name', 'wholesale_buyer_request', 'phone',]
        model = User

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].label = 'Ваше имя'
        self.fields['wholesale_buyer_request'].label = 'Я оптовый покупатель'


class SecurityCodeForm(forms.Form):
    security_code = forms.IntegerField(label='Код безопасности')






class ProfileEditingForm(forms.ModelForm):
    class Meta:
        fields = [
            'last_name',
            'first_name',
            'patronymic',
            'birth_date',
            'default_delivery',
            'email',
            'wholesale_buyer_request'
        ]
        model = User
        widgets={
            'birth_date': forms.SelectDateWidget(
                years=[i for i in range(
                    timezone.now().year - 18,
                    timezone.now().year - 101,
                    -1,
                )]
            )
        }

    def __init__(self, *args, **kwargs):
            super(ProfileEditingForm, self).__init__(*args, **kwargs)
            if 'instance' in kwargs and kwargs['instance'].buyer_type:
                self.fields.pop('wholesale_buyer_request')
            else:
                self.fields['wholesale_buyer_request'].label = 'Я оптовый покупатель'



LegalEntityFormSet = inlineformset_factory(
    User,
    LegalEntity,
    fields='__all__',
    max_num=3,
    extra=1,
)
