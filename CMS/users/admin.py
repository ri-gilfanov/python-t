from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from shop.models import LegalEntity


class LegalEntityInline(admin.StackedInline):
    model = LegalEntity
    extra = 1


@admin.register(User)
class UserAdmin(UserAdmin):
    def get_seller_buyer_count(self, obj):
        return str(obj.buyer_set.all().count())
    inlines = (LegalEntityInline,)
    search_fields = ('phone', 'last_name', 'first_name', 'patronymic')
    get_seller_buyer_count.short_description = 'покупателей'
    list_editable = ('buyer_type', 'is_seller')
    list_filter = ('wholesale_buyer_request', 'is_staff', 'is_superuser', 'is_active', 'groups')
    list_display = ('__str__', 'phone', 'email', 'wholesale_buyer_request', 'buyer_type', 'is_seller', 'get_seller_buyer_count')
    fieldsets = (
        ('Общая информация', {'fields': (
                'last_name',
                'first_name',
                'patronymic',
                'birth_date',
                'phone',
                'email',
                'password',
                'last_login',
                'date_joined',
        )}),
        ('Права доступа', {'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'is_seller',
                'groups',
                'user_permissions',
        )}),
        ('Карточка покупателя', {'fields': (
                    'buyer_type',
                    'seller',
                    'wholesale_buyer_request',
                    'default_delivery',
        )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2'),
        }),
    )
    raw_id_fields = ('seller',)
    ordering = None
    form = UserChangeForm
    add_form = UserCreationForm

    def get_queryset(self, request):
        queryset = super(UserAdmin, self).get_queryset(request).prefetch_related(
            'buyer_type',
            'buyer_set',
        )
        if request.user.is_seller and not request.user.is_superuser:
            return queryset.filter(seller=request.user)
        else:
            return queryset

    def get_formsets_with_inlines(self, request, obj=None):
        # не выводить инлайн-формы юр. лиц при создании пользователя
        for inline in self.get_inline_instances(request, obj):
            if isinstance(inline, LegalEntityInline) and obj is None:
                continue
            yield inline.get_formset(request, obj), inline
