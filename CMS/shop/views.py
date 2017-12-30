from django.shortcuts import render, redirect
from .models import Category, Order, Product, Receipt, LegalEntity
from .xml_parser import XMLProductUploader, XMLNechtoUploader
from core.view_functions import get_extend_paginator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.template.context_processors import csrf
from django.http import JsonResponse
import re
from mail_templated import send_mail
from django.core.urlresolvers import reverse
from core.sms import send_sms
from .filters import ProductFilter


def get_catalog(request):
    context = {}
    category_roots = Category.objects.filter(parent=None)
    context['category_menu'] = category_roots
    return render(request, 'shop/catalog.html', context)


@csrf_exempt
def get_category(request, pk=None, page_number=None):
    context = {}
    category = Category.objects.get(pk=pk)
    category_children = category.get_children()
    relations = category.relations.all()
    context['category_bread_crumbs'] = category.get_ancestors()
    context['category'] = category
    context['relations'] = relations
    # категория с подкатегориями
    if category_children:
        categories = category.get_descendants().filter(level__lte=category.level+2)
        context['categories'] = categories
        context['category_menu'] = category_children
        context['categories'] = categories
        template = 'shop/category.html'
        
    # категория с товарами
    else:
        category = Category.objects.filter(pk=pk)
        obj_list = Product.objects.filter(category=category).prefetch_related(
            'photo_set',
            'price_set__buyer_type',
            'price_set__product',
            'decimalattribute_set__filter__category',
            'rangeattribute_set__filter__category',
            'variantattribute_set__filter__category',
            'variantattribute_set__values',
            'variantattribute_set__filter__variant_set__filter',
        )
        filter_ = ProductFilter(request.GET, queryset=obj_list, request=request, strict=False)
        context['filter'] = filter_
        get_extend_paginator(context, filter_.qs, page_number, per_page=24)
        context['products'] = obj_list
        context['url_paginator_page'] = 'category'
        context['obj'] = category[0]
        template = 'shop/category_products.html'
    return render(request, template, context)


def get_product(request, pk):
    context = {}
    products = Product.objects.prefetch_related(
        'photo_set',
        'quantity_set__store',
        'price_set__buyer_type',
        'variantattribute_set__values',
        'decimalattribute_set',
        'rangeattribute_set',
    )
    product = products.get(pk=pk)
    context['category_bread_crumbs'] = product.category.get_ancestors(include_self=True)
    context['product'] = product
    return render(request, 'shop/product.html', context)



def parse_xml(request):
    if 'password' in request.GET and 'one_s_xml_parsing_12345678' == request.GET['password']:
        xml_product_uploader = XMLProductUploader()
        xml_product_uploader.run()
        xml_nechto_uploader = XMLNechtoUploader()
        xml_nechto_uploader.run()
    return redirect('/')



def get_cart(request):
    context = {}
    
    context.update(csrf(request))
    if 'cart' in request.session:
        product_list = list(request.session['cart'].keys())
        product_list = Product.objects.filter(pk__in=product_list).prefetch_related(
            'photo_set',
            'price_set__buyer_type',
            'price_set__product',
        )
        context['product_list'] = product_list
    if request.POST and 'method' in request.POST:
        if 'clear_cart' == request.POST['method']:
            request.session.pop('cart')
        if 'make_an_order' == request.POST['method']:
            if 'delivery' in request.POST and request.POST['delivery']:
                delivery = request.POST['delivery']
            else:
                delivery = ''
            if 'legal_entity' in request.POST and request.POST['legal_entity']:
                legal_entity = LegalEntity.objects.get(pk=int(request.POST['legal_entity']))
            else:
                legal_entity = None
            receipt = Receipt(buyer=request.user, delivery=delivery, legal_entity=legal_entity)
            receipt.save()
            Order.objects.bulk_create([
                    Order(
                        quantity=v,
                        product=Product.objects.get(pk=k),
                        receipt=receipt,
                    )
                    for k, v in request.session['cart'].items()
                ]
            )
            receipt.save()
            request.session.pop('cart')
            context = {'buyer': receipt.buyer, 'receipt': receipt}
            recipient_list = []
            for email in [receipt.buyer.seller.email]:
                if email:
                    recipient_list.append(email)
            send_mail('shop/receipt_email.html', context, from_email='piton-t@piton-t.ru', recipient_list=recipient_list)
            send_sms(recipient=receipt.buyer.seller.phone, text='Поступил заказ от клиента')
            return redirect(reverse('buyer_receipt', kwargs={'pk': receipt.pk}))
    return render(request, 'shop/cart.html', context)


@csrf_exempt
def request_to_cart(request):
    reqPOST = request.POST
    cart = request.session['cart'] if 'cart' in request.session else {}
    pk = reqPOST['pk'] if 'pk' in reqPOST else None
    method = reqPOST['method'] if 'method' in reqPOST else None

    if 'cart__set_product' == method and pk:
        quantity = reqPOST['quantity'] if 'quantity' in reqPOST else ''
        quantity = int(quantity) if quantity.isdigit() else 1
        cart.update({pk: quantity if quantity else 1})
        request.session.__setitem__('cart', cart)

    elif 'cart__unset_product' == method and pk:
        cart.pop(pk)
        request.session.__setitem__('cart', cart)

    elif 'cart__clear_cart' == method:
        request.session.pop('cart')

    if request.is_ajax():
        return JsonResponse({'статус': 'Успех'})


from .models import DecimalAttribute, RangeAttribute, VariantAttribute
from django.db.models import Count

def print_products(request):
    '''
    print(Product.objects.exclude(weight=None).count())
    print(Product.objects.exclude(height=None).count())
    print(Product.objects.exclude(depth=None).count())
    print(Product.objects.exclude(width=None).count())
    print(Product.objects.exclude(volume=None).count())
    with_brand = 0
    with_photo = 0
    with_description = 0
    with_decimalattribute = 0
    with_rangeattribute = 0
    with_variantattribute = 0
    l = Product.objects.filter(
        category__in=[5, 6, 9, 10, 11, 13, 14, 18, 20, 21, 22, 24, 25, 26, 16, 3, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 63, 64, 29, 28, 33, 34, 35, 36, 37, 38, 39, 30, 31]
    ).prefetch_related('brand', 'photo_set', 'decimalattribute_set', 'rangeattribute_set', 'variantattribute_set')
    for p in l:
    
        if p.brand is not None:
            with_brand += 1

        if p.photo_set.count() > 0:
            with_photo += 1

        if p.description != '':
            with_description += 1

        tmp = 0
        for attr in p.decimalattribute_set.all():
            if attr.value > 0:
                with_decimalattribute += 1
                break

        tmp = 0
        for attr in p.rangeattribute_set.all():
            if attr.values and (attr.values.lower or attr.values.upper):
                with_rangeattribute += 1
                break

        tmp = 0
        for attr in p.variantattribute_set.all():
            if attr.values.all():
                with_variantattribute += 1
                break
    
    
    print('всего', len(l))
    print('с брендом', with_brand)
    print('с фото', with_photo)
    print('с описанием', with_description)
    print('с числами', with_decimalattribute)
    print('с диапазонами', with_rangeattribute)
    print('с вариантами', with_variantattribute)

    '''
    '''
    category_id_list = [5, 6, 9, 10, 11, 13, 14, 18, 20, 21, 22, 24, 25, 26, 16, 3, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 63, 64, 29, 28, 33, 34, 35, 36, 37, 38, 39, 30, 31]
    #for category_id in category_id_list:
    products = Product.objects.filter(category__in=category_id_list).prefetch_related(
        'brand',
        'photo_set',
        'decimalattribute_set',
        'rangeattribute_set',
        'variantattribute_set',
    )
    print('всего', products.count())
    print('с фото', products.exclude(photo=None).count())
    print('с фото', products.annotate(num_photos=Count('photo')).filter(num_photos__gt=0).count())
    print('с описанием', products.exclude(description='').count())
    print('с брендом', products.exclude(brand=None).count())
    print('с ЧХ', products.exclude(decimalattribute__value__gt=1).count())
    print('с ДХ', products.exclude(rangeattribute__values=None).count())
    print('с ВХ', products.exclude(variantattribute__values=None).count())
    print('с весом', products.exclude(weight=None).count())
    print('с высотой', products.exclude(height=None).count())
    print('с глубиной', products.exclude(depth=None).count())
    print('с шириной', products.exclude(width=None).count())
    print('с объёмом', products.exclude(volume=None).count())
    #return redirect('/')
    '''
    pass
    '''
    from lxml import etree
    products = Product.objects.filter().prefetch_related(
        'brand',
        'photo_set',
    )
    xml_document = etree.Element('products')
    count = products.count()
    i = 0
    j = 0
    k = 0
    for product in products:
        photos = product.photo_set.all()
        photos_count = photos.count()
        if product.description or photos_count:
            i += 1
            print('Товаров: ', i, '\\', count)
            xml_product = etree.SubElement(xml_document, 'product')
            if product.description:
                j += 1
                print('Товаров с описанием: ', j, '\\', count)
                xml_description = etree.SubElement(xml_product, 'description').text = product.description
            xml_one_s_id = etree.SubElement(xml_product, 'one_s_id').text = product.one_s_id
            if photos_count:
                k += 1
                print('Товаров с фото: ', k, '\\', count)
                xml_photos = etree.SubElement(xml_document, 'photos')
                for photo in product.photo_set.all():
                    xml_photo = etree.SubElement(xml_photos, 'photo').text = photo.file.name
    file_ = open('/home/vom/Рабочий стол/products.xml', 'wb')
    file_.write(etree.tostring(xml_document, pretty_print=True, encoding='utf-8', xml_declaration=True))
    file_.close()
    '''
