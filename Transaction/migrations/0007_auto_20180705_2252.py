# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-07-05 17:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('Transaction', '0006_auto_20180516_2000'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='status',
        ),
        migrations.AddField(
            model_name='transaction',
            name='complete',
            field=models.BooleanField(default=False),
        ),
    ]
