# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-08-09 11:16
from __future__ import unicode_literals

import Homes.Bookings.utils
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Bookings', '0026_bookingfacility_quantity_acknowledged'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingMoveInDigitalSignature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signature', models.ImageField(upload_to=Homes.Bookings.utils.get_tenant_digital_signature_while_move_in_upload_path)),
                ('booking', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signatures', to='Bookings.Booking')),
            ],
        ),
    ]
