# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-06-18 08:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0027_auto_20190618_1247'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenantlatecheckin',
            name='current_booking',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='Bookings.Booking'),
            preserve_default=False,
        ),
    ]
