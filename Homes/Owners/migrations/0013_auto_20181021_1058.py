# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-10-21 05:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Owners', '0012_auto_20180901_1624'),
    ]

    operations = [
        migrations.RenameField(
            model_name='owner',
            old_name='parent_name',
            new_name='correspondant_name',
        ),
        migrations.RenameField(
            model_name='owner',
            old_name='parent_phone_no',
            new_name='correspondant_phone_no',
        ),
        migrations.AddField(
            model_name='owner',
            name='correspondant_relation',
            field=models.CharField(blank=True, choices=[('Son of', 'S/o'), ('Daughter of', 'D/o'), ('Wife of', 'W/o')], max_length=10, null=True),
        ),
    ]
