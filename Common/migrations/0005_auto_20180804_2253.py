# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-04 17:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Common', '0004_paymentcategory'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='paymentcategory',
            options={'verbose_name_plural': 'Payment Categories'},
        ),
    ]
