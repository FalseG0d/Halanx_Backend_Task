# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-04 13:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0002_house_bhk_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sharedroom',
            name='bed_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
