# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-06-18 09:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0029_occupation_vendor'),
        ('Tenants', '0030_tenantmeal_meal'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenantmeal',
            name='house',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='Houses.House'),
            preserve_default=False,
        ),
    ]