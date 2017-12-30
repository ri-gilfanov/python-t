from django.core.management.base import BaseCommand, CommandError
from ...xml_parser import XMLProductUploader, XMLNechtoUploader

class Command(BaseCommand):
    help = 'Импорт товаров, цен и остатков'

    def add_arguments(self, parser):
        parser.add_argument('files_type', type=str)

    def handle(self, *args, **options):
        if options['files_type'] == 'products':
            xml_product_uploader = XMLProductUploader()
            xml_product_uploader.run()
            self.stdout.write(self.style.SUCCESS('Загрузка товаров завершена'))
        elif options['files_type'] == 'offers':
            xml_product_uploader = XMLNechtoUploader()
            xml_product_uploader.run()
            self.stdout.write(self.style.SUCCESS('Загрузка цен и остатков завершена'))
