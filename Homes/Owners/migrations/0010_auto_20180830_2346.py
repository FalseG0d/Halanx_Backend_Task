# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-30 18:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Owners', '0009_ownerpayment_transaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ownerpayment',
            name='transaction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Transaction.HouseOwnerTransaction'),
        ),
    ]