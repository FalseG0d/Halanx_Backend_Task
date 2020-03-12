# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-11-14 14:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Transaction', '0016_auto_20181114_1834'),
    ]

    operations = [
        migrations.AddField(
            model_name='customertransaction',
            name='actual_collection_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='houseownertransaction',
            name='actual_collection_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='storetransaction',
            name='actual_collection_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]