# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-18 17:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0012_customer_is_registered'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='DOB',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='Gender',
            field=models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('others', 'Others')],
                                   max_length=10, null=True),
        ),
    ]
