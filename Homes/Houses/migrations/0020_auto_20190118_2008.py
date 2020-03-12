# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-01-18 14:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0019_auto_20190114_2134'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='spacemonthlyexpense',
            name='space',
        ),
        migrations.AddField(
            model_name='spacemonthlyexpense',
            name='house',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='monthly_expenses', to='Houses.House'),
        ),
        migrations.AddField(
            model_name='spacemonthlyexpense',
            name='space_subtype',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Houses.SpaceSubType'),
        ),
        migrations.AddField(
            model_name='spacesubtype',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
