# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-31 05:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0047_auto_20180331_1039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='follows',
            field=models.ManyToManyField(related_name='followed_by', to='UserBase.Customer'),
        ),
    ]
