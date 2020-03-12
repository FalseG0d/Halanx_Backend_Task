# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-08-09 11:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Bookings', '0027_bookingmoveindigitalsignature'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookingmoveindigitalsignature',
            name='booking',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signatures', to='Bookings.Booking'),
        ),
    ]
