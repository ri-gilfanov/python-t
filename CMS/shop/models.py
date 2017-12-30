from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.db.models.signals import post_delete
from django.conf import settings
from bulk_update.manager import BulkUpdateManager
from django.utils import timezone
from datetime import timedelta
from django.contrib.postgres.fields import FloatRangeField
from django.core.validators import DecimalValidator, MaxValueValidator, MinValueValidator
from .xml_generator import create_receipt


""" Раздел 1. Бренды, категории и товары """


class Brand(models.Model):
    """Бренд"""
    name = models.CharField('название', max_length=64, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'бренд'
        verbose_name_plural = 'бренды'


class Category(MPTTModel):
    """Категория"""
    name = models.CharField('название', max_length=64)
    cover = models.ImageField('обложка', upload_to='categories/%Y/%m/%d/', blank=True, null=True)
    parent = TreeForeignKey('self', models.CASCADE, blank=True, db_index=True, null=True, related_name='children',
                            verbose_name='родительская категория')
    relations = TreeManyToManyField('self', blank=True, verbose_name='связанные категории')
    one_s_ids = models.TextField('Идентификаторы категорий в 1С', blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        '''Удаление файла обложки категории при обновлении/удалении обложки'''
        try:
            post_object = self
            pre_object = post_object.__class__.objects.get(id=post_object.id)
            if pre_object.cover != post_object.cover:
                pre_object.cover.delete(save=False)
        except:
            pass
        super(self.__class__, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'


def del_category_cover_file(sender, **kwargs):
    try:
        object_ = kwargs.get('instance')
        storage, path = object_.cover.storage, object_.cover.path
        storage.delete(path)
    except:
        pass


post_delete.connect(del_category_cover_file, Category)


class Product(models.Model):
    """Товар"""
    brand = models.ForeignKey(Brand, models.CASCADE, blank=True, null=True, verbose_name='бренд')
    category = TreeForeignKey(Category, models.CASCADE, verbose_name='категория', null=True, blank=True)
    name = models.CharField('наименование товара', max_length=128)
    vendor_code = models.CharField('артикул', max_length=36, null=True, blank=True)
    one_s_id = models.CharField('идентификатор 1С', max_length=36, null=True, unique=True)
    description = RichTextUploadingField('описание товара', blank=True, config_name='default')
    base_price = models.DecimalField('базовая цена', max_digits=8, decimal_places=2, default=0)
    bp_source = models.CharField('источник базовой цены', max_length=36, blank=True, null=True)
    weight = models.DecimalField('вес с упаковкой (брутто), кг.', max_digits=7, decimal_places=3, blank=True, null=True)
    height = models.IntegerField('высота, мм.', blank=True, null=True)
    depth = models.IntegerField('глубина, мм.', blank=True, null=True)
    width = models.IntegerField('ширина, мм.', blank=True, null=True)
    volume = models.DecimalField('объём с упаковкой, м3', max_digits=7, decimal_places=3, blank=True, null=True)
    objects = BulkUpdateManager()

    def save(self, *args, **kwargs):
        super(Product, self).save(*args, **kwargs)
        """Обновление атрибутов товаров при сохранении"""
        category = self.category
        
        added_decimal_filters = category.decimalfilter_set.all()
        added_variant_filters = category.variantfilter_set.all()
        added_range_filters = category.rangefilter_set.all()

        added_decimal_attributes = self.decimalattribute_set.all()
        added_variant_attributes = self.variantattribute_set.all()
        added_range_attributes = self.rangeattribute_set.all()
        
        deleted_decimal_attributes = []
        deleted_variant_attributes = []
        deleted_range_attributes = []

        # удаление неактуальных атрибутов
        for decimal_attribute in added_decimal_attributes:
            if decimal_attribute.filter not in added_decimal_filters:
                deleted_decimal_attributes.append(decimal_attribute)

        for variant_attribute in added_variant_attributes:
            if variant_attribute.filter not in added_variant_filters:
                deleted_variant_attributes.append(variant_attribute)

        for range_attribute in added_range_attributes:
            if range_attribute.filter not in added_range_filters:
                deleted_range_attributes.append(range_attribute)

        deleted_da_ids = [a.id for a in deleted_decimal_attributes]
        deleted_va_ids = [a.id for a in deleted_variant_attributes]
        deleted_ra_ids = [a.id for a in deleted_range_attributes]

        DecimalAttribute.objects.filter(id__in=deleted_da_ids).delete()
        VariantAttribute.objects.filter(id__in=deleted_va_ids).delete()
        RangeAttribute.objects.filter(id__in=deleted_ra_ids).delete()

        # добавление новых атрибутов
        not_added_decimal_attributes = []
        not_added_variant_attributes = []
        not_added_range_attributes = []
        
        ready_da_ids = [i[0] for i in added_decimal_attributes.values_list('filter_id')]
        ready_va_ids = [i[0] for i in added_variant_attributes.values_list('filter_id')]
        ready_ra_ids = [i[0] for i in added_range_attributes.values_list('filter_id')]
        
        for decimal_filter in added_decimal_filters:
            if decimal_filter.id not in ready_da_ids:
                decimal_attribute = DecimalAttribute(product_id=self.id, filter=decimal_filter)
                not_added_decimal_attributes.append(decimal_attribute)
        
        for variant_filter in added_variant_filters:
            if variant_filter.id not in ready_va_ids:
                variant_attribute = VariantAttribute(product_id=self.id, filter=variant_filter)
                not_added_variant_attributes.append(variant_attribute)
        
        for range_filter in added_range_filters:
            if range_filter.id not in ready_ra_ids:
                range_attribute = RangeAttribute(product_id=self.id, filter=range_filter)
                not_added_range_attributes.append(range_attribute)
        
        DecimalAttribute.objects.bulk_create(not_added_decimal_attributes)
        VariantAttribute.objects.bulk_create(not_added_variant_attributes)
        RangeAttribute.objects.bulk_create(not_added_range_attributes)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-base_price']
        verbose_name = 'товар'
        verbose_name_plural = 'товары'


""" Раздел 2. Атрибуты категорий и товаров """


class VariantFilter(models.Model):
    """Атрибут категории выборочный"""
    name = models.CharField('название фильтра', max_length=64)
    category = TreeForeignKey(Category, models.CASCADE, verbose_name='категория')
    position = models.PositiveSmallIntegerField('позиция', blank=True, null=True)

    def save(self, *args, **kwargs):
        """создание вариативных атрибутов товаров при сохранении фильтра"""
        super(VariantFilter, self).save(*args, **kwargs)
        category = self.category
        category_products_ids = [i[0] for i in Product.objects.filter(category=category).values_list('id')]
        added_attributes = VariantAttribute.objects.filter(filter=self, product_id__in=category_products_ids)
        not_added_attributes = []
        ready_products_ids = [i[0] for i in added_attributes.values_list('product_id')]
        for i in category_products_ids:
            if i not in ready_products_ids:
                decimal_attribute = VariantAttribute(product_id=i, filter=self)
                not_added_attributes.append(decimal_attribute)
        VariantAttribute.objects.bulk_create(not_added_attributes)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'фильтр-выбор'
        verbose_name_plural = 'фильтры-выбор'
        unique_together = (('name', 'category'),)


class Variant(models.Model):
    """Атрибут категории числовой"""
    value = models.CharField('значение', max_length=64)
    filter = models.ForeignKey(VariantFilter, models.CASCADE)
    position = models.PositiveSmallIntegerField('позиция', blank=True, null=True)

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = 'значение фильтра-выбор'
        verbose_name_plural = 'значения фильтра-выбор'


class VariantAttribute(models.Model):
    """Атрибут категории числовой"""
    product = models.ForeignKey(Product, models.CASCADE, verbose_name='товар')
    filter = models.ForeignKey(VariantFilter, models.CASCADE, verbose_name='атрибут')
    values = models.ManyToManyField(Variant, blank=True, verbose_name='значения')


    def __str__(self):
        return str(self.filter.name)

    class Meta:
        verbose_name = 'атрибут-выбор'
        verbose_name_plural = 'атрибуты-выбор'
        unique_together = (('product', 'filter'),)


class DecimalFilter(models.Model):
    """Атрибут категории числовой"""
    name = models.CharField('название фильтра', max_length=64)
    category = TreeForeignKey(Category, models.CASCADE, verbose_name='категория')
    unit = models.CharField('единица измерения', max_length=64, blank=True)
    position = models.PositiveSmallIntegerField('позиция', blank=True, null=True)

    def save(self, *args, **kwargs):
        """создание числовых атрибутов товаров при сохранении фильтра"""
        super(DecimalFilter, self).save(*args, **kwargs)
        category = self.category
        category_products_ids = [i[0] for i in Product.objects.filter(category=category).values_list('id')]
        added_attributes = DecimalAttribute.objects.filter(filter=self, product_id__in=category_products_ids)
        not_added_attributes = []
        ready_products_ids = [i[0] for i in added_attributes.values_list('product_id')]
        for i in category_products_ids:
            if i not in ready_products_ids:
                decimal_attribute = DecimalAttribute(product_id=i, filter=self)
                not_added_attributes.append(decimal_attribute)
        DecimalAttribute.objects.bulk_create(not_added_attributes)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'фильтр-число'
        verbose_name_plural = 'фильтры-число'
        unique_together = (('name', 'category'),)


class DecimalAttribute(models.Model):
    """Атрибут товара числовой"""
    product = models.ForeignKey(Product, models.CASCADE, verbose_name='товар')
    filter = models.ForeignKey(DecimalFilter, models.CASCADE, verbose_name='атрибут')
    value = models.DecimalField('значение', default=0, max_digits=9, decimal_places=4, blank=True)

    def __str__(self):
        return str(self.filter.name)

    class Meta:
        verbose_name = 'атрибут-число'
        verbose_name_plural = 'атрибуты-число'
        unique_together = (('product', 'filter'),)


class RangeFilter(models.Model):
    """Атрибут категории числовой"""
    name = models.CharField('название фильтра', max_length=64)
    category = TreeForeignKey(Category, models.CASCADE, verbose_name='категория')
    unit = models.CharField('единица измерения', max_length=64, blank=True)
    position = models.PositiveSmallIntegerField('позиция', blank=True, null=True)

    def save(self, *args, **kwargs):
        """создание диапазонных атрибутов товаров при сохранении фильтра"""
        super(RangeFilter, self).save(*args, **kwargs)
        category = self.category
        category_products_ids = [i[0] for i in Product.objects.filter(category=category).values_list('id')]
        added_attributes = RangeAttribute.objects.filter(filter=self, product_id__in=category_products_ids)
        not_added_attributes = []
        ready_products_ids = [i[0] for i in added_attributes.values_list('product_id')]
        for i in category_products_ids:
            if i not in ready_products_ids:
                range_attribute = RangeAttribute(product_id=i, filter=self)
                not_added_attributes.append(range_attribute)
        RangeAttribute.objects.bulk_create(not_added_attributes)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'фильтр-диапазон'
        verbose_name_plural = 'фильтры-диапазон'
        unique_together = (('name', 'category'),)


class RangeAttribute(models.Model):
    """Атрибут товара диапазонный"""
    product = models.ForeignKey(Product, models.CASCADE, verbose_name='товар')
    filter = models.ForeignKey(RangeFilter, models.CASCADE, verbose_name='атрибут')
    values = FloatRangeField('диапазон значений', blank=True, null=True)

    def __str__(self):
        return str(self.filter.name)

    class Meta:
        verbose_name = 'атрибут-диапазон'
        verbose_name_plural = 'атрибуты-диапазон'
        unique_together = (('product', 'filter'),)


""" Раздел 3. Типы покупателей и цены """


class BuyerType(models.Model):
    """Тип покупателя"""
    name = models.CharField('название', max_length=64, unique=True)
    one_s_id = models.CharField('идентификатор 1С', max_length=36, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'тип покупателя'
        verbose_name_plural = 'типы покупателей'


class Price(models.Model):
    """Цена товара"""
    product = models.ForeignKey(Product, models.CASCADE, verbose_name='товар')
    buyer_type = models.ForeignKey(BuyerType, models.CASCADE, verbose_name='тип покупателя')
    value = models.DecimalField('цена', max_digits=8, decimal_places=2)
    objects = BulkUpdateManager()

    class Meta:
        verbose_name = 'цена товара'
        verbose_name_plural = 'цены товара'
        unique_together = (('product', 'buyer_type'),)


""" Раздел 4. Склады и остатки """


class Store(models.Model):
    """Магазины"""
    name = models.CharField('название', max_length=64, unique=True)
    one_s_id = models.CharField('идентификатор 1С', max_length=36, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'магазин'
        verbose_name_plural = 'магазины'


class Quantity(models.Model):
    """Остатки товаров на складах"""
    store = models.ForeignKey(Store, models.CASCADE, verbose_name='магазин')
    product = models.ForeignKey(Product, models.CASCADE, verbose_name='товар')
    value = models.DecimalField('количество', max_digits=8, decimal_places=2)
    objects = BulkUpdateManager()

    class Meta:
        verbose_name = 'остаток'
        verbose_name_plural = 'остатки'
        unique_together = (('store', 'product'),)


""" Раздел 5. Фотографии товаров """


class Photo(models.Model):
    """Фотография товара"""
    product = models.ForeignKey(Product, models.CASCADE, verbose_name='товар')
    file = models.ImageField('фотография', upload_to='products/%Y/%m/%d/')
    position = models.PositiveSmallIntegerField('позиция', blank=True, null=True)

    def save(self, *args, **kwargs):
        try:
            post_object = self
            pre_object = post_object.__class__.objects.get(id=post_object.id)
            if pre_object.file != post_object.file:
                pre_object.file.delete(save=False)
        except:
            pass
        super(self.__class__, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'фотография'
        verbose_name_plural = 'фотографии'
        ordering = ['position']


def del_photo_file(sender, **kwargs):
    try:
        object_ = kwargs.get('instance')
        storage, path = object_.file.storage, object_.file.path
        storage.delete(path)
    except:
        pass


post_delete.connect(del_photo_file, Photo)


""" Раздел 6. Адреса доставки и заказы """


class LegalEntity(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, verbose_name='клиент')
    name = models.CharField('название', max_length=128)
    taxpayer_id = models.CharField('ИНН', max_length=12, unique=True)
    reason_code = models.CharField('КПП', max_length=9)
    legal_address = models.TextField('юридический адрес', max_length=256, blank=True)
    phone = models.DecimalField(
        'номер телефона',
        max_digits=10,
        decimal_places=0,
        validators=[MaxValueValidator(9999999999), MinValueValidator(1000000000)],
        error_messages={
            'min_value': 'Номер телефона указывается без восьмёрки, должен содержать 10 цифр и не должен начинаться с 0',
            'unique': 'Пользователь с таким номера телефона уже существует',
        },
    )
    email = models.EmailField('электронная почта', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'юридическое лицо'
        verbose_name_plural = 'юридические лица'


class Receipt(models.Model):
    def get_really_up_to():
        return timezone.now() + timedelta(days=3)

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, verbose_name='клиент')
    delivery = models.TextField('адрес доставки', max_length=256, blank=True)
    legal_entity = models.ForeignKey(LegalEntity, models.CASCADE, blank=True, null=True, verbose_name='юридическое лицо')
    really_up_to = models.DateTimeField('действительно до', default=get_really_up_to)
    paid_amount = models.DecimalField('внесённая сумма', max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        super(Receipt, self).save(*args, **kwargs)
        if self.order_set.exists():
            create_receipt(self)

    def get_paid_amount(self):
        return float(self.paid_amount)

    @property
    def total_price(self):
        orders = self.order_set.all()
        total = 0
        for order in orders:
            for price in order.product.price_set.all():
                if price.buyer_type == self.buyer.buyer_type:
                    total += price.value
        return total

    def __str__(self):
        return 'Счёт №%i' % (self.pk)

    class Meta:
        ordering = ['-id']
        verbose_name = 'счёт на оплату'
        verbose_name_plural = 'счета на оплату'


class Order(models.Model):
    product = models.ForeignKey(Product, models.CASCADE, verbose_name='товар')
    quantity = models.PositiveSmallIntegerField('кол-во', default=1)
    receipt = models.ForeignKey(Receipt, models.CASCADE, verbose_name='счёт на оплату')
    status = models.CharField(
        'статус позиции заказа',
        max_length=32,
        choices=(
            ('processed', 'в обработке'),
            ('accepted', 'принято'),
            ('shipped', 'отгружено'),
            ('canceled', 'отменено'),
        ),
        default='processed',
    )

    def __str__(self):
        return 'Заказ №%i' % (self.pk)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
