# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-07-30 11:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Owners', '0022_auto_20190730_1637'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownerlisting',
            name='furnish_type',
            field=models.CharField(blank=True, choices=[('full', 'Fully furnished'), ('semi', 'Semi furnished'), ('nil', 'Unfurnished')], max_length=100, null=True),
        ),
    ]
