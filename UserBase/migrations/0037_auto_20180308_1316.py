# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-08 07:46
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0036_userlocation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='education',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='education',
                                    to='UserBase.Customer'),
        ),
        migrations.AlterField(
            model_name='userlocation',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='locations',
                                    to='UserBase.Customer'),
        ),
        migrations.AlterField(
            model_name='work',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='work',
                                    to='UserBase.Customer'),
        ),
    ]
