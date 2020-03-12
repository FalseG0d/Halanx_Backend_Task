# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-06 12:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0007_auto_20180806_1525'),
    ]

    operations = [
        migrations.AlterField(
            model_name='house',
            name='application',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='house', to='Houses.HouseApplication'),
        ),
    ]