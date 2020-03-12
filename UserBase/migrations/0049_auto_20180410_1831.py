# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-10 13:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0048_auto_20180331_1049'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='follows',
            field=models.ManyToManyField(blank=True, related_name='followed_by', to='UserBase.Customer'),
        ),
    ]
