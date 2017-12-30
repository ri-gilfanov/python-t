import django_filters
from .models import (
    Brand, Product, Price,
    DecimalAttribute, DecimalFilter,
    RangeAttribute, RangeFilter,
    VariantAttribute, VariantFilter, Variant,
)
from django import forms
from django.db.models import Max
from psycopg2.extras import NumericRange
from decimal import Decimal
from .widgets import JRangeWidget
from django.db.models import Q


class ProductFilter(django_filters.FilterSet):
    price = django_filters.CharFilter(
        label='Цена',
        method='filter_price',
        widget=JRangeWidget(),
    )
    brand = django_filters.ModelMultipleChoiceFilter(queryset=Brand.objects.all(), widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        self.base_filters = self.declared_filters.copy()
        # BRAND
        brand_ids = list(set(t[0] for t in kwargs['queryset'].exclude(brand=None).values_list('brand')))
        self.base_filters['brand'].queryset = Brand.objects.filter(id__in=brand_ids)

        # PRICE
        if kwargs['request'].user.is_authenticated() and kwargs['request'].user.buyer_type:
            prices = Price.objects.filter(buyer_type=kwargs['request'].user.buyer_type, product__in=kwargs['queryset'])
            max_price = prices.aggregate(Max('value'))['value__max']
        else:
            max_price = kwargs['queryset'].aggregate(Max('base_price'))['base_price__max']

        max_price = max_price + 1 if max_price else 1
        max_price = str(max_price)
        self.base_filters['price'].widget.attrs['max'] = max_price
 
        self.base_filters['price'].widget.attrs['value'] = kwargs['request'].GET.get('price', default='%s,%s' % ('0', str(max_price)))

        # ATTRIBUTES
        category_list = set(kwargs['queryset'].values_list('category', flat=True))

        if category_list and len(category_list) == 1:
            category = tuple(set(category_list))[0]

            decimal_filters = DecimalFilter.objects.filter(category=category)
            for f in decimal_filters:
                attributes = DecimalAttribute.objects.filter(filter=f)
                max_value = attributes.aggregate(Max('value'))['value__max']
                max_value = max_value + 1 if max_value else 1
                self.base_filters['da_%i' % f.id] = django_filters.CharFilter(
                    label=f.name,
                    method='filter_decimal_attribute',
                    name='da_%i' % f.id,
                    widget=JRangeWidget(attrs={'max': str(max_value)}),
                )
                value = kwargs['request'].GET.get('da_%i' % f.id, default='%s,%s' % ('0', str(max_value)))
                self.base_filters['da_%i' % f.id].widget.attrs['value'] = value

            range_filters = RangeFilter.objects.filter(category=category)
            for f in range_filters:
                attributes = RangeAttribute.objects.filter(filter=f)
                max_value = max([i.upper for i in attributes.values_list('values', flat=True) if i])
                max_value = max_value + 1 if max_value else 1
                self.base_filters['ra_%i' % f.id] = django_filters.CharFilter(
                    label=f.name,
                    name='ra_%i' % f.id,
                    method='filter_range_attribute',
                    widget=JRangeWidget(attrs={'max': str(max_value)}),
                )
                value = kwargs['request'].GET.get('ra_%i' % f.id, default='%s,%s' % ('0', str(max_value)))
                self.base_filters['ra_%i' % f.id].widget.attrs['value'] = value

            variant_filters = VariantFilter.objects.filter(category=category)
            for f in variant_filters:
                self.base_filters['va_%i' % f.id] = django_filters.ModelMultipleChoiceFilter(
                    label=f.name,
                    method='filter_variant_attribute',
                    name='va_%i' % f.id,
                    queryset=f.variant_set.all(),
                    widget=forms.CheckboxSelectMultiple,
                )

        super(ProductFilter, self).__init__(*args, **kwargs)

    def filter_price(self, queryset, name, value):
        d = {}
        value = value.split(',')
        value = [int(float(ch)) for ch in value]
        if value[0] or value[1]:
            if self.request.user.is_authenticated() and self.request.user.buyer_type:
                d['price__buyer_type'] = self.request.user.buyer_type
                field_name = 'price__value'
            else:
                field_name = 'base_price'

            if value[0] and value[1]:
                d['%s__range' % field_name] = value[0], value[1]
            elif value[0]:
                d['%s__gte' % field_name] = value[0]
            elif value[1]:
                d['%s__lte' % field_name] = value[1]
                d
            return queryset.filter(Q(**d) | Q(**{'%s%s' % (field_name, '__isnull'): True}))
        else:
            return queryset.filter()

    def filter_decimal_attribute(self, queryset, name, value):
        value = value.split(',')
        value = [int(float(ch)) for ch in value]
        if value[0] or value[1]:
            filter_ = DecimalFilter.objects.get(pk=int(name[3:]))
            attributes = DecimalAttribute.objects.filter(filter=filter_)
            if value[0] and value[1]:
                attributes = attributes.filter(Q(value__range=(value[0], value[1])) | Q(value__isnull=True))
            elif value[0]:
                attributes = attributes.filter(Q(value__gte=value[0]) | Q(value__isnull=True))
            elif value[1]:
                attributes = attributes.filter(Q(value__lte=value[1]) | Q(value__isnull=True))
            return queryset.filter(decimalattribute__in=attributes)
        else:
            return queryset.filter()

    def filter_range_attribute(self, queryset, name, value):
        value = value.split(',')
        value = [int(float(ch)) for ch in value]
        if value[0] or value[1]:
            filter_ = RangeFilter.objects.get(pk=int(name[3:]))
            attributes = RangeAttribute.objects.filter(filter=filter_)
            if value[0] and value[1]:
                attributes = attributes.filter(Q(values__contained_by=(value[0], value[1])) | Q(values__isnull=True))
            elif value[0]:
                attributes = attributes.filter(Q(values__contained_by=NumericRange(value[0], None)) | Q(values__isnull=True))
            elif value[1]:
                attributes = attributes.filter(Q(values__contained_by=NumericRange(0, value[1])) | Q(values__isnull=True))
            return queryset.filter(rangeattribute__in=attributes)
        else:
            return queryset.filter()

    def filter_variant_attribute(self, queryset, name, value):
        if value:
            return queryset.filter(variantattribute__values__in=value)
        else:
            return queryset.filter()

    class Meta:
        model = Product
        fields = ['price', 'brand']
