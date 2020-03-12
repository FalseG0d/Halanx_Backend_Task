# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-10-22 17:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Bookings', '0006_auto_20181022_2236'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='facilities',
        ),
        migrations.AddField(
            model_name='bookingfacility',
            name='booking',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Bookings.Booking'),
        ),
    ]
