# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-06-19 05:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0032_auto_20190618_1639'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tenant',
            name='added_by',
        ),
    ]
