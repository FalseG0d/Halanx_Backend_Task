# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-02-20 15:55
from __future__ import unicode_literals

from django.db import migrations, models

import UserBase.models


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0034_auto_20180206_2248'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='FbTemplate',
            field=models.ImageField(blank=True, null=True, upload_to=UserBase.models.get_fb_template_upload_path),
        ),
    ]
