# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-06-20 10:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Owners', '0024_teammember_houses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teammember',
            name='about',
            field=models.TextField(blank=True, max_length=100, null=True),
        ),
    ]
