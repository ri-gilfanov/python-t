from lxml import etree
from datetime import datetime
from os import chmod


def create_receipt(receipt):
    receipt_id = str(receipt.id)
    receipt_date = datetime.now().strftime('%Y-%m-%d')
    receipt_time = datetime.now().strftime('%H:%M:%S')
    total_price = str(receipt.total_price)

    # 1. Коммерческая информация
    коммерческая_информация = etree.Element('КоммерческаяИнформация')
    коммерческая_информация.set('ВерсияСхемы', '2.03')
    коммерческая_информация.set('ДатаФормирования', receipt_date)
    
    # 1.1. Документ
    документ = etree.SubElement(коммерческая_информация, 'Документ')
    etree.SubElement(документ, 'Ид').text = receipt_id
    etree.SubElement(документ, 'Номер').text = receipt_id
    etree.SubElement(документ, 'Дата').text = receipt_date
    etree.SubElement(документ, 'Время').text = receipt_time
    etree.SubElement(документ, 'Роль').text = 'Продавец'
    etree.SubElement(документ, 'Валюта').text = 'руб'
    etree.SubElement(документ, 'Курс').text = '1'
    etree.SubElement(документ, 'Сумма').text = total_price

    # 1.1.1. Контрагенты
    контрагенты = etree.SubElement(документ, 'Контрагенты')
    контрагент = etree.SubElement(контрагенты, 'Контрагент')
    etree.SubElement(контрагент, 'Роль').text = 'Покупатель'
    etree.SubElement(контрагент, 'ИдТипаЦеныПокупателя').text = receipt.buyer.buyer_type.one_s_id
    if not receipt.legal_entity:
        etree.SubElement(контрагент, 'Наименование').text = receipt.buyer.get_full_name()
        etree.SubElement(контрагент, 'ПолноеНаименование').text = receipt.buyer.get_full_name()
        etree.SubElement(контрагент, 'Фамилия').text = receipt.buyer.last_name
        etree.SubElement(контрагент, 'Имя').text = receipt.buyer.first_name
    else:
        etree.SubElement(контрагент, 'Наименование').text = receipt.legal_entity.name
        etree.SubElement(контрагент, 'ОфициальноеНаименование').text = receipt.legal_entity.name
        etree.SubElement(контрагент, 'ИНН').text = receipt.legal_entity.taxpayer_id
        etree.SubElement(контрагент, 'КПП').text = receipt.legal_entity.reason_code
        юридический_адрес = etree.SubElement(контрагент, 'ЮридическийАдрес')
        etree.SubElement(юридический_адрес, 'Представление').text = receipt.legal_entity.legal_address
    адрес = etree.SubElement(контрагент, 'Адрес')
    etree.SubElement(адрес, 'Представление').text = receipt.delivery

    # контакты
    контакты = etree.SubElement(контрагент, 'Контакты')
    if not receipt.legal_entity:
        контакт = etree.SubElement(контакты, 'Контакт')
        etree.SubElement(контакт, 'Тип').text = 'ТелефонРабочий'
        etree.SubElement(контакт, 'Значение').text = '+7' + str(receipt.buyer.phone)
        контакт = etree.SubElement(контакты, 'Контакт')
        etree.SubElement(контакт, 'Тип').text = 'Почта'
        etree.SubElement(контакт, 'Значение').text = receipt.buyer.email
    else:
        контакт = etree.SubElement(контакты, 'Контакт')
        etree.SubElement(контакт, 'Тип').text = 'ТелефонРабочий'
        etree.SubElement(контакт, 'Значение').text = '+7' + str(receipt.legal_entity.phone)
        контакт = etree.SubElement(контакты, 'Контакт')
        etree.SubElement(контакт, 'Тип').text = 'Почта'
        etree.SubElement(контакт, 'Значение').text = receipt.legal_entity.email
    
    # 1.2. Товары
    товары = etree.SubElement(документ, 'Товары')
    for order in receipt.order_set.all():
        товар = etree.SubElement(товары, 'Товар')
        etree.SubElement(товар, 'Ид').text = order.product.one_s_id
        etree.SubElement(товар, 'Наименование').text = order.product.name
        etree.SubElement(товар, 'Артикул').text = order.product.vendor_code
        etree.SubElement(товар, 'Количество').text = str(order.quantity)
        for price in order.product.price_set.all():
            if price.buyer_type == receipt.buyer.buyer_type:
                product_price = str(price.value)
                break
        else:
            product_price = str(order.product.base_price)
        etree.SubElement(товар, 'ЦенаЗаЕдиницу').text = product_price
        etree.SubElement(товар, 'Сумма').text = product_price * order.quantity
        значения_реквизитов = etree.SubElement(товар, 'ЗначенияРеквизитов')
        значение_реквизита = etree.SubElement(значения_реквизитов, 'ЗначениеРеквизита')
        etree.SubElement(значение_реквизита, 'Наименование').text = 'ВидНоменклатуры'
        etree.SubElement(значение_реквизита, 'Значение').text = 'Товар'
        значение_реквизита = etree.SubElement(значения_реквизитов, 'ЗначениеРеквизита')
        etree.SubElement(значение_реквизита, 'Наименование').text = 'ТипНоменклатуры'
        etree.SubElement(значение_реквизита, 'Значение').text = 'Товар'

    # 1.3. Значения реквизитов
    значения_реквизитов = etree.SubElement(документ, 'ЗначенияРеквизитов')
    # 1.3.1 Значения реквизитов
    значение_реквизита = etree.SubElement(значения_реквизитов, 'ЗначениеРеквизита')
    наименование = etree.SubElement(значение_реквизита, 'Наименование').text = 'Статус заказа'
    значение = etree.SubElement(значение_реквизита, 'Значение').text = 'Не согласован'

    handle = etree.tostring(коммерческая_информация, pretty_print=True, encoding='utf-8', xml_declaration=True)
    applic = open('files/orders_export/' + receipt_id + '.xml', 'wb')
    applic.write(handle)
    applic.close()
    chmod(r'files/orders_export/' + str(receipt_id) + '.xml', 0o665)
