# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-21 16:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0042_customer_region'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customer',
            old_name='region',
            new_name='Region',
        ),
    ]
