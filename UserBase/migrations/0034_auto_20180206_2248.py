# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-02-06 17:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0033_customer_last_visit'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='AppVersion',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='cLatitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='cLongitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
