from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField


class CustomPage(models.Model):
    title = models.CharField('заголовок страницы', max_length=128)
    content = RichTextUploadingField('содержание страницы', blank=True, config_name='default')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'произвольная страницы'
        verbose_name_plural = 'произвольные страницы'
