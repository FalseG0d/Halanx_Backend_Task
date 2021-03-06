# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-12-20 15:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0019_auto_20181220_2114'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenantpayment',
            name='amount',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='tenantpayment',
            name='original_amount',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
