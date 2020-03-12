# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-13 14:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('AreaManagers', '0001_initial'),
        ('Houses', '0009_remove_flat_bhk_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='housevisit',
            name='area_manager',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='house_visits', to='AreaManagers.AreaManager'),
        ),
    ]