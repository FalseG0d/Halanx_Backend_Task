# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-06-17 09:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Owners', '0021_teammember_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='teammember',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
