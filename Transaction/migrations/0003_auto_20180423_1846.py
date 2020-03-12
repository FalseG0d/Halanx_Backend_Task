# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-23 13:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('Transaction', '0002_auto_20180423_1831'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='platform',
            field=models.CharField(blank=True, choices=[('web', 'web'), ('android', 'androids')], max_length=20,
                                   null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='payment_gateway_type',
            field=models.CharField(blank=True, choices=[('payu', 'payu'), ('paytm', 'paytm')], max_length=20,
                                   null=True),
        ),
    ]