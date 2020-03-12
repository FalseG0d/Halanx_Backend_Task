# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-21 15:16
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('Places', '0012_region'),
        ('UserBase', '0041_customer_is_visible'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='Places.Region'),
        ),
    ]
