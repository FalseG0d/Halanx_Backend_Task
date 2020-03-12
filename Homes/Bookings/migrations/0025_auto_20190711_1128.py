# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-07-11 05:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Bookings', '0024_booking_promo_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='onboarding_charges',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='booking',
            name='token_amount',
            field=models.FloatField(default=400.0),
        ),
    ]