# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-09-01 10:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Owners', '0010_auto_20180830_2346'),
    ]

    operations = [
        migrations.AddField(
            model_name='owner',
            name='dob',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
