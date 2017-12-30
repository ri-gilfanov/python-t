from os import listdir, remove
from xmltodict import parse
from collections import OrderedDict
from .models import BuyerType, Brand, Product, Category, Store, Price, Quantity
from decimal import Decimal
import re
import gc
from time import time


'''
склады
    склад Мангазея
        50f13546-176f-11e6-923a-001e678b9924
    Основной
        c8aab876-9a15-11e3-80c1-001e678b9924

кол-во не выводить
    есть в наличии
    уточняйте наличие

базовая цена:
    Для сайта Розничная или
        4340bc9e-169f-11e7-b961-001e678b9924
    Для сайта Розничная Мангазея
        54bc5598-16a0-11e7-b961-001e678b9924


нужные цены:
    Для сайта ТТ
        dfc7f962-169f-11e7-b961-001e678b9924
    Для сайта Максимум
        f22ebca0-169f-11e7-b961-001e678b9924
    Для сайта Спец
        b2b188d3-169f-11e7-b961-001e678b9924
    Для сайта Спец1
        c8015ac5-169f-11e7-b961-001e678b9924
    Для сайта Опт
        9f8794bd-169f-11e7-b961-001e678b9924
'''




class XMLAbstractUploader(object):
    def __init__(self):
        """Инициализация"""
        self.file_path_pattern = 'files/products_import/'
        self.file_name_pattern = 'import'
        self.file_names = None
        self.category_id_correlation = None

    def get_file_names(self):
        file_names = listdir(self.file_path_pattern)
        file_names = filter(lambda n: self.file_name_pattern in n, file_names)
        return file_names

    def run(self):
        start = time()
        for file_name in self.file_names:
            before = time()
            with open(self.file_path_pattern + file_name, 'r') as file:
                try:
                    xml = file.read()
                    xml = parse(xml)
                    xml = xml['КоммерческаяИнформация']
                    self.upload_part(xml)
                except:
                    print('Не удалось прочитать: ', file_name)
            remove(self.file_path_pattern + file_name)
        if self.file_name_pattern == 'import':
            print('Загрузка товаров заняла ', time() - start, ' секунд.')

    def upload_part(self, xml):
        pass


class XMLProductUploader(XMLAbstractUploader):
    """XML загрузчик товаров"""

    def __init__(self):
        """Инициализация"""
        super(XMLProductUploader, self).__init__()
        self.file_name_pattern = 'import'
        self.file_names = self.get_file_names()
        self.category_id_correlation = self.get_category_id_correlation()

    def get_category_id_correlation(self):
        """Получить соотнесение ид категорий из 1C и БД"""
        category_id_list_dict = Category.objects.all().values('id', 'one_s_ids')
        [c.update({'one_s_ids': c['one_s_ids'].split('\r\n')}) for c in category_id_list_dict if c['one_s_ids']]
        return category_id_list_dict

    def upload_part(self, xml):
        xml_products = xml['Каталог']['Товары']['Товар']
        one_s_product_ids = [p['Ид'] for p in xml_products]
        added_products = list(Product.objects.filter(one_s_id__in=one_s_product_ids).only('name', 'vendor_code', 'category_id', 'one_s_id').all())
        not_added_products = []
        added_product_one_s_id = [p.one_s_id for p in added_products]
        not_added_product_one_s_id = [i for i in one_s_product_ids if i not in one_s_product_ids]
        for xml_product in xml_products:
            name = self.product_name_normalize(xml_product['Наименование'])
            vendor_code = xml_product['Артикул']
            one_s_id = xml_product['Ид']
            xml_category_id = xml_product['Группы']['Ид'] if 'Группы' in xml_product else ''
            category_ids = [d['id'] for d in self.category_id_correlation if xml_category_id in d['one_s_ids']]
            category_id = category_ids[0] if len(category_ids) else None
            if category_id:
                if xml_product['Ид'] in added_product_one_s_id:
                    product = [p for p in added_products if p.one_s_id == xml_product['Ид']][0]
                    product.name = name
                    product.vendor_code = vendor_code
                    product.category_id = category_id
                    product.one_s_id = one_s_id
                else:
                    product = Product(name=name, vendor_code=vendor_code, category_id=category_id, one_s_id=one_s_id)
                    not_added_products.append(product)
        Product.objects.bulk_create(not_added_products)
        Product.objects.bulk_update(added_products, update_fields=['name', 'vendor_code', 'category_id', 'one_s_id'])

    def product_name_normalize(self, string):
        numeric_list = re.findall('(\d+)', string)
        has_double_space = string.find('  ')
        if numeric_list or has_double_space != -1:
            if numeric_list and string.find(numeric_list[0]) == 0:
                string = string[len(numeric_list[0]):]
                while string.find('  ') != -1:
                    string = string.replace('  ', ' ')
                string = string.strip()
        return string


class XMLNechtoUploader(XMLAbstractUploader):
    """XML загрузчик цен и остатков"""

    def __init__(self):
        """Инициализация"""
        super(XMLNechtoUploader, self).__init__()
        self.file_name_pattern = 'offer'
        self.file_names = self.get_file_names()
        self.buyer_types = BuyerType.objects.only('id', 'one_s_id').all()
        self.stores = Store.objects.only('id', 'one_s_id').all()
        self.stores_one_s_ids = ('50f13546-176f-11e6-923a-001e678b9924', 'c8aab876-9a15-11e3-80c1-001e678b9924')


    def upload_part(self, xml):
        xml_offers = xml['ПакетПредложений']['Предложения']['Предложение']
        if type(xml_offers) is list:
            one_s_product_ids = [o['Ид'] for o in xml_offers]

            added_products = list(Product.objects.filter(one_s_id__in=one_s_product_ids).only('id', 'one_s_id', 'bp_source', 'base_price').all())

            added_prices = Price.objects.select_related('buyer_type', 'product').filter(product__in=added_products)
            not_added_prices = []

            added_quantities = Quantity.objects.select_related('store', 'product').filter(product__in=added_products)
            not_added_quantities = []

            for xml_offer in xml_offers:
                xml_price_type_id = xml_offer['Цены']['Цена']['ИдТипаЦены']
                temp_product_list = [p for p in added_products if p.one_s_id == xml_offer['Ид']]
                product = temp_product_list[0] if temp_product_list else None

                if product:
                    price_value = Decimal(xml_offer['Цены']['Цена']['ЦенаЗаЕдиницу'])

                    # базовая цена
                    retail_price_standart = '4340bc9e-169f-11e7-b961-001e678b9924'
                    retail_price_mangazeya = '54bc5598-16a0-11e7-b961-001e678b9924'
                    if price_value > 0:
                        if xml_price_type_id == retail_price_standart:
                            product.base_price = price_value
                            product.bp_source = retail_price_standart
                        elif (
                            xml_price_type_id == retail_price_mangazeya
                            and product.bp_source != retail_price_standart
                        ):
                            product.base_price = price_value
                            product.bp_source = retail_price_mangazeya

                    # цены по типу покупателей
                    temp_buyer_type_list = [bt for bt in self.buyer_types if bt.one_s_id == xml_price_type_id]
                    if temp_buyer_type_list:
                        buyer_type = temp_buyer_type_list[0]
                        product_added_prices = [p for p in added_prices if p.product.one_s_id == xml_offer['Ид']]
                        temp_product_added_prices = [p for p in product_added_prices if p.buyer_type == buyer_type]
                        price = temp_product_added_prices[0] if temp_product_added_prices else None
                        if price:
                            price.value = price_value
                        elif xml_price_type_id not in [p.buyer_type.one_s_id for p in product_added_prices]:
                            price = Price(buyer_type=buyer_type, product=product, value=price_value)
                            not_added_prices.append(price)

                    # остатки на складах
                    product_added_quantities = [q for q in added_quantities if q.product.one_s_id == xml_offer['Ид']]
                    product_added_quantities_one_s_ids = [q.store.one_s_id for q in product_added_quantities]
                    for xml_store in xml_offer['Склад']:
                        if xml_store['@ИдСклада'] in product_added_quantities_one_s_ids:
                            quantity = [q for q in product_added_quantities if q.store.one_s_id == xml_store['@ИдСклада']][0]
                            quantity.value = Decimal(xml_store['@КоличествоНаСкладе'])
                        elif xml_store['@ИдСклада'] in self.stores_one_s_ids:
                            temp_store_list = [s for s in self.stores if s.one_s_id == xml_store['@ИдСклада']]
                            if temp_store_list:
                                store = temp_store_list[0]
                                quantity = Quantity(product=product, store=store, value=Decimal(xml_store['@КоличествоНаСкладе']))
                                not_added_quantities.append(quantity)

            Product.objects.bulk_update(added_products, update_fields=['base_price', 'bp_source'])
            Price.objects.bulk_create(not_added_prices)
            Price.objects.bulk_update(added_prices, update_fields=['value'])
            Quantity.objects.bulk_create(not_added_quantities)
            Quantity.objects.bulk_update(added_quantities, update_fields=['value'])







from collections import OrderedDict


brand_dict = OrderedDict([
    ('ADL', ['d2dd8866-8406-11e4-80d7-001e678b9924']),
    ('ALSO', ['fb6232e9-c187-11e4-9c7d-001e678b9924']),
    ('APE', ['fb6232fc-c187-11e4-9c7d-001e678b9924']),
    ('APRIORI', ['c8bd6f93-2939-11e6-84dd-001e678b9924']),
    ('ARISTON', ['6d77fe04-6924-11e6-ae7e-001e678b9924', 'fb623302-c187-11e4-9c7d-001e678b9924']),
    ('ATMOR', ['c188cbbf-50a9-11e6-95ad-001e678b9924']),
    ('AYVAZ', ['fb623304-c187-11e4-9c7d-001e678b9924']),
    ('Aquaheat', ['bcded40b-be4b-11e4-9c7d-001e678b9924']),
    ('Armaflex', ['cab0c92c-fbca-11e5-b508-001e678b9924']),
    ('Ascot', ['e77e729b-c3b8-11e4-9c7d-001e678b9924']),
    ('BAUERTHERM', ['a03d9362-2ba7-11e5-af70-001e678b9924']),
    ('BAXI', ['f08818fc-da68-11e3-bf36-cf15df66cb5c', 'c80b97c4-c2f0-11e4-9c7d-001e678b9924', '2b3e88c5-4003-11e6-98a1-001e678b9924', 'c80b97c3-c2f0-11e4-9c7d-001e678b9924']),
    ('BOSCH', ['62e68258-077b-11e6-ada7-001e678b9924']),
    ('BREEZE', ['e77e7294-c3b8-11e4-9c7d-001e678b9924']),
    ('BUDERUS', ['8a060c76-d118-11e4-9c7d-001e678b9924']),
    ('BUGATTI', ['fb62331f-c187-11e4-9c7d-001e678b9924']),
    ('BVR', ['d3192010-090f-11e6-bc0d-001e678b9924']),
    ('Ballomax', ['e77e7295-c3b8-11e4-9c7d-001e678b9924']),
    ('Ballorex', ['fb62331d-c187-11e4-9c7d-001e678b9924']),
    ('Belamos', ['bcded408-be4b-11e4-9c7d-001e678b9924']),
    ('CIMM', ['bcded405-be4b-11e4-9c7d-001e678b9924']),
    ('COMAP', ['fb623319-c187-11e4-9c7d-001e678b9924', 'fb62331c-c187-11e4-9c7d-001e678b9924']),
    ('Ci', ['fb6232e5-c187-11e4-9c7d-001e678b9924', 'fb6232e6-c187-11e4-9c7d-001e678b9924', 'fb6232e4-c187-11e4-9c7d-001e678b9924', 'fb6232ea-c187-11e4-9c7d-001e678b9924', 'fb6232e8-c187-11e4-9c7d-001e678b9924']),
    ('DAB', ['061a6bd5-c8a7-11e5-b9e2-001e678b9924']),
    ('DANFOS', ['df551dbc-2d69-11e6-8512-001e678b9924', '85ee0453-c8d1-11e6-bed0-001e678b9924', '36bcda4d-c8d2-11e6-bed0-001e678b9924', '10edea29-c8db-11e6-bed0-001e678b9924', '610662df-c19f-11e5-b9e2-001e678b9924', 'd1c28422-2d68-11e6-8512-001e678b9924', 'e1ee283f-2d68-11e6-8512-001e678b9924', '74a47530-2d69-11e6-8512-001e678b9924']),
    ('DE', ['c80b97d0-c2f0-11e4-9c7d-001e678b9924']),
    ('DIANA', ['e77e729a-c3b8-11e4-9c7d-001e678b9924']),
    ('Daewoo', ['c80b97cb-c2f0-11e4-9c7d-001e678b9924']),
    ('Danfoss', ['b9a81c8f-81e9-11e4-80d7-001e678b9924', '0180282c-2d68-11e6-8512-001e678b9924']),
    ('Drazice', ['bcded411-be4b-11e4-9c7d-001e678b9924']),
    ('ELSOTHERM', ['c8bd6f94-2939-11e6-84dd-001e678b9924']),
    ('ETALON', ['c80b97b0-c2f0-11e4-9c7d-001e678b9924']),
    ('EUROS', ['bf0912aa-610b-11e6-8b57-001e678b9924']),
    ('Electrolux', ['c80b97ca-c2f0-11e4-9c7d-001e678b9924', 'c80b97c9-c2f0-11e4-9c7d-001e678b9924', 'adae7f0e-da5a-11e3-bf36-cf15df66cb5c']),
    ('FAR', ['fb623314-c187-11e4-9c7d-001e678b9924', 'a0b6b4e9-da69-11e3-bf36-cf15df66cb5c', 'c80b97c1-c2f0-11e4-9c7d-001e678b9924', 'd319200d-090f-11e6-bc0d-001e678b9924']),
    ('FLEXSY', ['fb6232fa-c187-11e4-9c7d-001e678b9924']),
    ('Fondital', ['c80b97cd-c2f0-11e4-9c7d-001e678b9924']),
    ('Funke', ['d2dd886e-8406-11e4-80d7-001e678b9924']),
    ('GENIALE', ['6fd1e1a4-f7f5-11e5-b508-001e678b9924']),
    ('GROSS', ['7452fbaf-392e-11e6-98a1-001e678b9924']),
    ('Garanterm', ['c80b97ae-c2f0-11e4-9c7d-001e678b9924']),
    ('Geniale', ['bcded416-be4b-11e4-9c7d-001e678b9924']),
    ('Giacomini', ['138790ae-9c77-11e4-a082-001e678b9924']),
    ('Global', ['bcded419-be4b-11e4-9c7d-001e678b9924']),
    ('Gorenie', ['610662e0-c19f-11e5-b9e2-001e678b9924']),
    ('Grundfos', ['398e0f88-799a-11e6-98f3-001e678b9924', '154bebe3-b591-11e4-bd1a-001e678b9924', 'f36fa12c-da55-11e3-bf36-cf15df66cb5c', 'e77e728c-c3b8-11e4-9c7d-001e678b9924', 'e77e7287-c3b8-11e4-9c7d-001e678b9924']),
    ('HAIER', ['ac17fb06-9d8b-11e5-9cb6-001e678b9924', 'ac17fb00-9d8b-11e5-9cb6-001e678b9924']),
    ('Haiba', ['e77e7262-c3b8-11e4-9c7d-001e678b9924']),
    ('Henrad', ['6fd1e1a7-f7f5-11e5-b508-001e678b9924']),
    ('ICMA', ['fb62331a-c187-11e4-9c7d-001e678b9924', 'acacbb68-2f93-11e6-8512-001e678b9924', 'd3192009-090f-11e6-bc0d-001e678b9924']),
    ('IDDIS', ['e77e7299-c3b8-11e4-9c7d-001e678b9924']),
    ('IMI', ['d2dd885f-8406-11e4-80d7-001e678b9924']),
    ('ITAP', ['fb6232ee-c187-11e4-9c7d-001e678b9924', 'e77e7293-c3b8-11e4-9c7d-001e678b9924', 'fb6232ef-c187-11e4-9c7d-001e678b9924', 'fb6232ec-c187-11e4-9c7d-001e678b9924', 'fb623300-c187-11e4-9c7d-001e678b9924', 'fb6232ed-c187-11e4-9c7d-001e678b9924', '6fd1e190-f7f5-11e5-b508-001e678b9924', 'b44fccc8-2f93-11e6-8512-001e678b9924', 'd319200e-090f-11e6-bc0d-001e678b9924']),
    ('JM', ['e77e728a-c3b8-11e4-9c7d-001e678b9924']),
    ('K-Flex', ['c80b97a0-c2f0-11e4-9c7d-001e678b9924']),
    ('KITLINE', ['bcded407-be4b-11e4-9c7d-001e678b9924', 'e77e7285-c3b8-11e4-9c7d-001e678b9924']),
    ('KOSPEL', ['c80b97d1-c2f0-11e4-9c7d-001e678b9924']),
    ('Klabb', ['e77e7264-c3b8-11e4-9c7d-001e678b9924']),
    ('Klever', ['e77e7263-c3b8-11e4-9c7d-001e678b9924']),
    ('LD', ['e2e16097-ce8b-11e3-80c5-001e678b9924']),
    ('Luxor', ['73b1f9cc-be45-11e4-9c7d-001e678b9924', 'd319200b-090f-11e6-bc0d-001e678b9924']),
    ('MASTER', ['c80b97cc-c2f0-11e4-9c7d-001e678b9924']),
    ('MEIBES', ['91173de6-59fa-11e6-8b57-001e678b9924']),
    ('MIXLINE', ['ad9e111f-5581-11e6-95ad-001e678b9924']),
    ('MagnaPlast', ['cab0c91f-fbca-11e5-b508-001e678b9924']),
    ('MeerPlast', ['f427b464-da64-11e3-bf36-cf15df66cb5c']),
    ('Milardo', ['c7ddaf37-7c13-11e6-98f3-001e678b9924']),
    ('NAVAL', ['e77e7297-c3b8-11e4-9c7d-001e678b9924']),
    ('NAVIEN', ['a3b6fd6c-4345-11e6-aabe-001e678b9924']),
    ('NTM', ['ff512b83-de7f-11e4-9c7d-001e678b9924', '67d74aa6-9a53-11e5-9cb6-001e678b9924']),
    ('NevaLux', ['c80b97cf-c2f0-11e4-9c7d-001e678b9924']),
    ('Oasis', ['fb62330a-c187-11e4-9c7d-001e678b9924']),
    ('Orkli', ['fb62331b-c187-11e4-9c7d-001e678b9924', 'd3192008-090f-11e6-bc0d-001e678b9924']),
    ('Ostendorf', ['48de97cf-e5d0-11e5-b9e2-001e678b9924']),
    ('Oventrop', ['bd8f8bd0-b777-11e4-bd1a-001e678b9924']),
    ('Potato', ['50ff9e88-badc-11e6-9674-001e678b9924']),
    ('Prado', ['8332e3d1-89b2-11e4-80d7-001e678b9924']),
    ('Pro', ['67d74aae-9a53-11e5-9cb6-001e678b9924']),
    ('ProFactor', ['03221c2e-a70e-11e6-81a6-001e678b9924', 'd373825d-0d3b-11e6-923a-001e678b9924', 'f6a6e7ec-65d8-11e6-8b57-001e678b9924', '13f21dab-2d43-11e6-8512-001e678b9924', 'a60c5bfc-799f-11e6-98f3-001e678b9924']),
    ('Protherm', ['c80b97c5-c2f0-11e4-9c7d-001e678b9924', 'bcded412-be4b-11e4-9c7d-001e678b9924', 'c80b97c6-c2f0-11e4-9c7d-001e678b9924', '468a893e-da69-11e3-bf36-cf15df66cb5c', '43cab998-4003-11e6-98a1-001e678b9924']),
    ('Purmo', ['d2dd884b-8406-11e4-80d7-001e678b9924']),
    ('Quartz', ['e77e729c-c3b8-11e4-9c7d-001e678b9924']),
    ('RBM', ['cab0c90d-fbca-11e5-b508-001e678b9924']),
    ('REHAU', ['a8488faf-f88f-11e5-b508-001e678b9924', '0eb79316-f888-11e5-b508-001e678b9924']),
    ('REMER', ['610662dc-c19f-11e5-b9e2-001e678b9924']),
    ('RUSANT', ['50cf4d96-f768-11e6-bcd7-001e678b9924']),
    ('Rifar', ['bcded415-be4b-11e4-9c7d-001e678b9924']),
    ('Royal', ['6fd1e1a6-f7f5-11e5-b508-001e678b9924', '403b4952-e106-11e5-b9e2-001e678b9924', '6fd1e196-f7f5-11e5-b508-001e678b9924']),
    ('SER', ['67d74aab-9a53-11e5-9cb6-001e678b9924', '67d74aa9-9a53-11e5-9cb6-001e678b9924', '67d74aaa-9a53-11e5-9cb6-001e678b9924', '6fd1e192-f7f5-11e5-b508-001e678b9924', 'f7ab27f9-da56-11e3-bf36-cf15df66cb5c']),
    ('SFA', ['e77e728d-c3b8-11e4-9c7d-001e678b9924']),
    ('SPK', ['fec95ec5-da5d-11e3-bf36-cf15df66cb5c']),
    ('STG-Viega', ['cab0c913-fbca-11e5-b508-001e678b9924']),
    ('STI', ['834cb2c3-9fca-11e5-9cb6-001e678b9924', 'bcded410-be4b-11e4-9c7d-001e678b9924', 'c80b97c0-c2f0-11e4-9c7d-001e678b9924', 'bcded3fd-be4b-11e4-9c7d-001e678b9924', '6fd1e19f-f7f5-11e5-b508-001e678b9924', '9e08ab73-c3b6-11e4-9c7d-001e678b9924', 'fb6232f1-c187-11e4-9c7d-001e678b9924', 'bcded40f-be4b-11e4-9c7d-001e678b9924', 'fb6232e2-c187-11e4-9c7d-001e678b9924', 'fb6232e3-c187-11e4-9c7d-001e678b9924', '6fd1e18f-f7f5-11e5-b508-001e678b9924', '0ae194af-da5d-11e3-bf36-cf15df66cb5c', 'fb6232f3-c187-11e4-9c7d-001e678b9924']),
    ('STM', ['6c037775-da54-11e3-bf36-cf15df66cb5c']),
    ('STOUT', ['53875fe0-146b-11e7-b961-001e678b9924', '6962fe6d-7fac-11e6-98f3-001e678b9924', 'db94b298-3f60-11e6-98a1-001e678b9924', 'c8bd6f7c-2939-11e6-84dd-001e678b9924', '5d8e398d-9cf3-11e6-ad81-001e678b9924']),
    ('Salus', ['fb62330b-c187-11e4-9c7d-001e678b9924']),
    ('Sensonic', ['c80b97a5-c2f0-11e4-9c7d-001e678b9924']),
    ('Siemens', ['154bebed-b591-11e4-bd1a-001e678b9924']),
    ('TAEN', ['6fd1e1a0-f7f5-11e5-b508-001e678b9924', '12fb322b-da5f-11e3-bf36-cf15df66cb5c', '7fc68f75-5895-11e6-95ad-001e678b9924', 'fb6232f7-c187-11e4-9c7d-001e678b9924', 'fb6232f8-c187-11e4-9c7d-001e678b9924', '67d74aa8-9a53-11e5-9cb6-001e678b9924', 'a46c3a6e-822e-11e6-98f3-001e678b9924', '574ebca0-509e-11e6-95ad-001e678b9924']),
    ('TECOFI', ['61f97528-5895-11e6-95ad-001e678b9924', '41997aa5-2d62-11e6-8512-001e678b9924', 'fa6b920f-0dbf-11e6-923a-001e678b9924']),
    ('THERMEX', ['fb623303-c187-11e4-9c7d-001e678b9924']),
    ('UNI-SFER', ['6fd1e195-f7f5-11e5-b508-001e678b9924']),
    ('UNIGB', ['7a0e5af3-d36b-11e4-9c7d-001e678b9924']),
    ('UNIPUMP', ['bcded403-be4b-11e4-9c7d-001e678b9924', 'e77e7282-c3b8-11e4-9c7d-001e678b9924', '68312852-da68-11e3-bf36-cf15df66cb5c', 'e77e728f-c3b8-11e4-9c7d-001e678b9924', 'e77e7281-c3b8-11e4-9c7d-001e678b9924', 'e77e7283-c3b8-11e4-9c7d-001e678b9924']),
    ('UPONOR', ['cab0c914-fbca-11e5-b508-001e678b9924']),
    ('VAILLANT', ['c80b97ce-c2f0-11e4-9c7d-001e678b9924']),
    ('VAREM', ['bcded409-be4b-11e4-9c7d-001e678b9924']),
    ('VESBO', ['4e73aa27-da64-11e3-bf36-cf15df66cb5c']),
    ('VRT', ['bda10f1c-c5cc-11e6-bee2-001e678b9924', '925326ec-c69b-11e6-bee2-001e678b9924']),
    ('Valtec', ['b6f6f69d-20b1-11e6-9573-001e678b9924']),
    ('Valtek', ['6fd1e170-f7f5-11e5-b508-001e678b9924']),
    ('Vogel&Noot', ['83b29df3-0957-11e7-9293-001e678b9924']),
    ('Vt', ['6fd1e194-f7f5-11e5-b508-001e678b9924', 'd319200c-090f-11e6-bc0d-001e678b9924']),
    ('WILO', ['e77e728b-c3b8-11e4-9c7d-001e678b9924', 'bcded3f6-be4b-11e4-9c7d-001e678b9924', '7d0ab139-014c-11e6-81f8-001e678b9924', '7d0ab13a-014c-11e6-81f8-001e678b9924', '7d0ab13b-014c-11e6-81f8-001e678b9924', '7d0ab143-014c-11e6-81f8-001e678b9924', '7d0ab144-014c-11e6-81f8-001e678b9924', '7d0ab145-014c-11e6-81f8-001e678b9924', '19c83a80-215c-11e6-9573-001e678b9924', '1f4239f7-bc7d-11e3-80c2-001e678b9924', '7d0ab13c-014c-11e6-81f8-001e678b9924', '7d0ab13d-014c-11e6-81f8-001e678b9924', '7d0ab13e-014c-11e6-81f8-001e678b9924', '7d0ab13f-014c-11e6-81f8-001e678b9924', '7d0ab140-014c-11e6-81f8-001e678b9924', '7d0ab141-014c-11e6-81f8-001e678b9924', 'e77e728e-c3b8-11e4-9c7d-001e678b9924', 'e77e7286-c3b8-11e4-9c7d-001e678b9924']),
    ('Watts', ['cb68c673-a4b1-11e5-88f2-001e678b9924', 'ac17fafb-9d8b-11e5-9cb6-001e678b9924']),
    ('Wester', ['ed363bda-f4a3-11e5-b733-001e678b9924', 'bcded404-be4b-11e4-9c7d-001e678b9924', '25f677f9-4020-11e6-98a1-001e678b9924', 'c80b97da-c2f0-11e4-9c7d-001e678b9924']),
    ('ZOTA', ['94448d32-f49c-11e5-b733-001e678b9924']),
    ('ZOX', ['f4c640c3-c5b7-11e6-bee2-001e678b9924']),
    ('Акватек', ['84f08637-2c7e-11e6-8512-001e678b9924', '8328d80b-650e-11e6-8b57-001e678b9924']),
    ('Бетар', ['49a1dc20-e3f3-11e4-9c7d-001e678b9924']),
    ('Бивал', ['e77e7298-c3b8-11e4-9c7d-001e678b9924']),
    ('Будерус', ['3aeb205f-fd3d-11e5-b508-001e678b9924']),
    ('Водолей', ['e77e7288-c3b8-11e4-9c7d-001e678b9924']),
    ('ГАЗ', ['c80b97a7-c2f0-11e4-9c7d-001e678b9924']),
    ('ГАЛМЕТ', ['efceb520-bb68-11e5-b9e2-001e678b9924']),
    ('Джилекс', ['1270f045-05f3-11e6-81f8-001e678b9924', '3700e703-2871-11e6-b2e8-001e678b9924']),
    ('ЗЕННЕР', ['9c2bf1b5-c2f1-11e4-9c7d-001e678b9924']),
    ('КАРАТ', ['c80b97bb-c2f0-11e4-9c7d-001e678b9924']),
    ('КОНТУР', ['acf70bb0-cfe3-11e5-b9e2-001e678b9924', 'b6f6f6b6-20b1-11e6-9573-001e678b9924', 'acf70bb1-cfe3-11e5-b9e2-001e678b9924', 'a8488fab-f88f-11e5-b508-001e678b9924', '728eca40-2146-11e5-9db1-001e678b9924', '3f8712e6-da58-11e3-bf36-cf15df66cb5c']),
    ('Керми', ['d2dd884d-8406-11e4-80d7-001e678b9924']),
    ('Крест', ['e6d8571e-bd24-11e6-bee2-001e678b9924']),
    ('ЛИДЕЯ', ['d2dd884c-8406-11e4-80d7-001e678b9924']),
    ('Лемакс', ['c80b97c8-c2f0-11e4-9c7d-001e678b9924']),
    ('МЕТЕР', ['bcded40d-be4b-11e4-9c7d-001e678b9924']),
    ('Макси-быт', ['c80b97db-c2f0-11e4-9c7d-001e678b9924']),
    ('Миномесс', ['bcded40c-be4b-11e4-9c7d-001e678b9924']),
    ('ПОЛИТЕК', ['a8488fac-f88f-11e5-b508-001e678b9924', 'cab0c91e-fbca-11e5-b508-001e678b9924']),
    ('ПОРИЛЕКС', ['fb6232f9-c187-11e4-9c7d-001e678b9924']),
    ('ППУ', ['810b1530-65fd-11e6-8b57-001e678b9924']),
    ('РусНИТ', ['81e553aa-2227-11e6-9573-001e678b9924']),
    ('САНТЕК', ['8cae99d5-c6e9-11e4-9c7d-001e678b9924', '8cae99d4-c6e9-11e4-9c7d-001e678b9924']),
    ('СИНИКОН', ['a8488faa-f88f-11e5-b508-001e678b9924']),
    ('СК', ['a8488fa9-f88f-11e5-b508-001e678b9924', 'a8488fae-f88f-11e5-b508-001e678b9924']),
    ('СТЛ', ['6fd1e1a1-f7f5-11e5-b508-001e678b9924']),
    ('СТМ', ['bf411346-08ae-11e7-9293-001e678b9924', '67d74aa5-9a53-11e5-9cb6-001e678b9924']),
    ('ТЕРМАФЛЕКС', ['bc0adc98-da5e-11e3-bf36-cf15df66cb5c']),
    ('ТЕХНОПЛЕКС', ['eb8dcf11-91b2-11e6-aa15-001e678b9924']),
    ('ТИЛИТ', ['cb68c68a-a4b1-11e5-88f2-001e678b9924']),
    ('ТеплоТех', ['bcded413-be4b-11e4-9c7d-001e678b9924']),
    ('ФММ', ['610662de-c19f-11e5-b9e2-001e678b9924']),
    ('ФМФ', ['fb6232e7-c187-11e4-9c7d-001e678b9924']),
    ('ХЕМКОР', ['a8488fad-f88f-11e5-b508-001e678b9924']),
    ('ЭВАН', ['8dd71c23-da61-11e3-bf36-cf15df66cb5c']),
    ('ЭКОМЕРА', ['bcded40e-be4b-11e4-9c7d-001e678b9924']),
    ('ЭНЕРГОФЛЕКС', ['d50668be-da5c-11e3-bf36-cf15df66cb5c']),
    ('Эверест', ['32493d5f-badc-11e6-9674-001e678b9924']),
    ('ЮГ', ['7d0ab146-014c-11e6-81f8-001e678b9924']),
])


class XMLProductBrander(XMLAbstractUploader):
    """XML загрузчик товаров"""

    def __init__(self):
        """Инициализация"""
        super(XMLProductBrander, self).__init__()
        self.file_name_pattern = 'import'
        self.file_names = self.get_file_names()

    def upload_part(self, xml):
        xml_products = xml['Каталог']['Товары']['Товар']
        for p in xml_products:
            product_one_s_id = p['Ид']
            if 'Группы' in p:
                category_one_s_id = p['Группы']['Ид']
                for key in brand_dict:
                    if category_one_s_id in brand_dict[key]:
                        products = Product.objects.filter(one_s_id=product_one_s_id)
                        if products:
                            brand, created = Brand.objects.get_or_create(name=key)
                            products[0].brand = brand
                            products[0].save()
