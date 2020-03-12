# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-11-04 06:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Transaction', '0012_auto_20181030_2124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customertransaction',
            name='payment_gateway',
            field=models.CharField(blank=True, choices=[('PayU', 'PayU'), ('Paytm', 'Paytm'), ('Pay via NEFT/IMPS', 'Pay via NEFT/IMPS'), ('Cash', 'Cash')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='houseownertransaction',
            name='payment_gateway',
            field=models.CharField(blank=True, choices=[('PayU', 'PayU'), ('Paytm', 'Paytm'), ('Pay via NEFT/IMPS', 'Pay via NEFT/IMPS'), ('Cash', 'Cash')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='storetransaction',
            name='payment_gateway',
            field=models.CharField(blank=True, choices=[('PayU', 'PayU'), ('Paytm', 'Paytm'), ('Pay via NEFT/IMPS', 'Pay via NEFT/IMPS'), ('Cash', 'Cash')], max_length=20, null=True),
        ),
    ]