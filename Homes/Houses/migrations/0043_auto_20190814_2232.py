# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-08-14 17:02
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0042_auto_20190814_1104'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vendor',
            name='houses',
        ),
        migrations.RemoveField(
            model_name='vendor',
            name='occupation',
        ),
        migrations.RemoveField(
            model_name='vendor',
            name='owner',
        ),
        migrations.DeleteModel(
            name='Vendor',
        ),
    ]
