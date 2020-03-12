# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-04 14:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0001_initial'),
        ('Common', '0004_paymentcategory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenantpayment',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='Common.PaymentCategory'),
        ),
    ]
