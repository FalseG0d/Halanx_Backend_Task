# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-06-18 11:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0031_tenantmeal_house'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenantmeal',
            name='house',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meals', to='Houses.House'),
        ),
    ]
