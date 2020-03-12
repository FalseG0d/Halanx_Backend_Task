# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-08 12:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0003_tenantdocument_verified'),
        ('Bookings', '0003_booking_tenant'),
    ]

    operations = [
        migrations.CreateModel(
            name='MonthlyRent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('rent', models.FloatField(default=0)),
                ('fine', models.FloatField(default=0)),
                ('booking', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='monthly_rents', to='Bookings.Booking')),
                ('payment', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment', to='Tenants.TenantPayment')),
            ],
        ),
    ]
