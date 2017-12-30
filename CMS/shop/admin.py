from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin, TreeRelatedFieldListFilter, MPTTModelAdmin
from .models import (
    Brand, Category, Product,
    VariantFilter, VariantAttribute, Variant,
    DecimalFilter, DecimalAttribute,
    RangeFilter, RangeAttribute,
    BuyerType, Price, Photo, Store, Quantity,
    Receipt, Order, LegalEntity
)
from users.models import User
import nested_admin


''' Бренды '''


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    def get_brand_product_count(self, obj):
        return str(obj.product_set.all().count())

    def get_queryset(self, request):
        return Brand.objects.all().prefetch_related(
            'product_set',
        )
    get_brand_product_count.short_description = 'товаров'
    search_fields = ['name']
    list_display = ['name', 'get_brand_product_count']


''' Категории '''




class VariantInline(nested_admin.NestedTabularInline):
    model = Variant
    sortable_field_name = "position"
    extra = 1


class VariantFilterInline(nested_admin.NestedTabularInline):
    model = VariantFilter
    sortable_field_name = "position"
    extra = 1
    inlines = [VariantInline]


class DecimalFilterInline(nested_admin.NestedTabularInline):
    model = DecimalFilter
    sortable_field_name = "position"
    extra = 1


class RangeFilterInline(nested_admin.NestedTabularInline):
    model = RangeFilter
    sortable_field_name = "position"
    extra = 1


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin, nested_admin.NestedModelAdmin):
    def get_category_product_count(self, obj):
        return str(obj.product_set.all().count())
    get_category_product_count.short_description = 'товаров'

    def get_queryset(self, request):
        return Category.objects.all().prefetch_related(
            'product_set',
        )

    inlines = [VariantFilterInline, DecimalFilterInline, RangeFilterInline]
    raw_id_fields = ['parent']
    search_fields = ['name', 'one_s_ids']
    list_display = ['tree_actions', 'indented_title', 'get_category_product_count']


""" Товары """


class PriceInline(admin.TabularInline):
    model = Price
    extra = 1

    def has_delete_permission(self, request, obj=None):
        return False


class QuantityInline(admin.TabularInline):
    model = Quantity
    extra = 1

    def has_delete_permission(self, request, obj=None):
        return False


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1


from django.forms import ModelForm


class VariantAttributeForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(VariantAttributeForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            self.fields['values'].queryset = Variant.objects.filter(filter=kwargs['instance'].filter)

    class Meta:
        model = VariantAttribute
        fields = '__all__'


class VariantAttributeInline(admin.TabularInline):
    model = VariantAttribute
    max_num = 0
    fields = ('filter', 'values',)
    readonly_fields = ('filter',)
    form = VariantAttributeForm

    def has_delete_permission(self, request, obj=None):
        return False


class DecimalAttributeInline(admin.TabularInline):
    model = DecimalAttribute
    max_num = 0
    fields = ('filter', 'value',)
    readonly_fields = ('filter',)

    def has_delete_permission(self, request, obj=None):
        return False


class RangeAttributeInline(admin.TabularInline):
    model = RangeAttribute
    max_num = 0
    fields = ('filter', 'values',)
    readonly_fields = ('filter',)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    def get_product_photo_count(self, obj):
        return obj.photo_set.all().count()

    def has_description(self, obj):
        return bool(obj.description)
    has_description.short_description = 'описание'
    has_description.boolean = True

    def get_queryset(self, request):
        return Product.objects.all().prefetch_related(
            'photo_set',
            'brand',
        )

    model = Product
    get_product_photo_count.short_description = 'фотографий'
    inlines = [PriceInline, QuantityInline, PhotoInline, VariantAttributeInline, DecimalAttributeInline, RangeAttributeInline]
    list_filter = (
        ('category', TreeRelatedFieldListFilter),
        'brand',
    )
    raw_id_fields = ['brand', 'category']
    list_display = ['name', 'vendor_code', 'brand', 'get_product_photo_count', 'has_description', 'base_price']
    search_fields = ['name', 'vendor_code']
    list_per_page = 300
    readonly_fields = ['bp_source']


""" Выборочные атрибуты """


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1


@admin.register(VariantFilter)
class VariantFilterAdmin(admin.ModelAdmin):
    inlines = [VariantInline]
    list_filter = (('category', TreeRelatedFieldListFilter),)


""" Типы покупателей """


@admin.register(BuyerType)
class BuyerTypeAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'one_s_id']


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    def get_store_quantity_count(self, obj):
        return str(obj.quantity_set.filter(value__gt=0).count())

    def get_queryset(self, request):
        return Store.objects.all().prefetch_related(
            'quantity_set',
        )
    get_store_quantity_count.short_description = 'товаров в наличии'
    search_fields = ['name']
    list_display = ['name', 'get_store_quantity_count']



""" Юридические лица и заказы """


@admin.register(LegalEntity)
class LegalEntityAdmin(admin.ModelAdmin):
    pass


class OrderInline(admin.TabularInline):
    model = Order
    extra = 1
    def get_product_vendor_code(self, obj):
        return obj.product.vendor_code
    get_product_vendor_code.short_description = 'артикул'


    raw_id_fields = ('product',)
    list_display = ('__str__', 'get_product_vendor_code', 'quantity',)


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    def get_buyer_seller(self, obj):
        return obj.buyer.seller
    get_buyer_seller.short_description = 'менеджер'

    def get_total_price(self, obj):
        return obj.total_price
    get_total_price.short_description = 'общая сумма'

    inlines = [OrderInline]
    list_display = ('__str__', 'buyer', 'get_buyer_seller', 'get_total_price', 'delivery',)
    raw_id_fields = ('buyer',)
    list_filter = (('buyer__seller', admin.RelatedOnlyFieldListFilter,),)

    def get_queryset(self, request):
        queryset = super(ReceiptAdmin, self).get_queryset(request).prefetch_related(
            'order_set__product__price_set__buyer_type',
        )
        if request.user.is_seller and not request.user.is_superuser:
            return queryset.filter(buyer__seller=request.user)
        else:
            return queryset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
            if db_field.name == 'buyer' and not request.user.is_superuser:
                kwargs['queryset'] = User.objects.filter(seller=request.user)
            return super(ReceiptAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
