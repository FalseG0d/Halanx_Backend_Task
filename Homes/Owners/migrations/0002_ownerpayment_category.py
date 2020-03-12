# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-04 14:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Common', '0004_paymentcategory'),
        ('Owners', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownerpayment',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='Common.PaymentCategory'),
        ),
    ]