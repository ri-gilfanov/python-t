# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-26 06:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_auto_20170424_1555'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='wholesale_buyer_request',
            field=models.BooleanField(default=False, verbose_name='Заявка оптового покупателя'),
        ),
    ]