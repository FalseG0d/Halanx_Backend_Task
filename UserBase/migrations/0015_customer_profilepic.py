# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-18 17:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0014_customer_bio'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='ProfilePic',
            field=models.ImageField(blank=True, null=True),
        ),
    ]
