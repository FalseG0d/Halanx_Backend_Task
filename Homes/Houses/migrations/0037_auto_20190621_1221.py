# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-06-21 06:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0036_auto_20190620_1804'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billsplit',
            name='paid',
            field=models.BooleanField(default=False),
        ),
    ]
