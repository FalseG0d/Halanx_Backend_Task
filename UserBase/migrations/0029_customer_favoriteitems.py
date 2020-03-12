# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-21 08:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('Products', '0018_product_taxpercentage'),
        ('UserBase', '0028_remove_customer_favoriteitems'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='FavoriteItems',
            field=models.ManyToManyField(blank=True, to='Products.Product'),
        ),
    ]