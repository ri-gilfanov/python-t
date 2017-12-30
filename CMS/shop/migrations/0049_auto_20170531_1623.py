# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-31 11:23
from __future__ import unicode_literals

import django.contrib.postgres.fields.ranges
from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0048_auto_20170530_1648'),
    ]

    operations = [
        migrations.CreateModel(
            name='RangeAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('values', django.contrib.postgres.fields.ranges.FloatRangeField(default=(0, 0), verbose_name='диапазон значений')),
            ],
            options={
                'verbose_name': 'атрибут диапазонный',
                'verbose_name_plural': 'атрибуты диапазонный',
            },
        ),
        migrations.CreateModel(
            name='RangeFilter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, verbose_name='имя фильтра')),
                ('category', mptt.fields.TreeForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.Category', verbose_name='категория')),
            ],
            options={
                'verbose_name': 'фильтр числовой',
                'verbose_name_plural': 'фильтры числовые',
            },
        ),
        migrations.AddField(
            model_name='rangeattribute',
            name='filter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.RangeFilter', verbose_name='атрибут'),
        ),
        migrations.AddField(
            model_name='rangeattribute',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.Product', verbose_name='товар'),
        ),
        migrations.AlterUniqueTogether(
            name='rangefilter',
            unique_together=set([('name', 'category')]),
        ),
        migrations.AlterUniqueTogether(
            name='rangeattribute',
            unique_together=set([('product', 'filter')]),
        ),
    ]