# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-08-17 06:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Owners', '0027_tenantgroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='owneraddressdetail',
            name='zone',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
