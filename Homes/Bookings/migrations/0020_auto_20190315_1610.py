# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-03-15 10:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Bookings', '0019_auto_20190308_2321'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monthlyrent',
            name='payment',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='monthly_rent', to='Tenants.TenantPayment'),
        ),
    ]
