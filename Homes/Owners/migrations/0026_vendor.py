# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-08-14 17:02
from __future__ import unicode_literals

import Homes.Houses.utils
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0043_auto_20190814_2232'),
        ('Owners', '0025_auto_20190620_1542'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('phone_no', models.CharField(max_length=15)),
                ('profile_pic', models.ImageField(blank=True, null=True, upload_to=Homes.Houses.utils.get_vendor_profile_pic_upload_path)),
                ('houses', models.ManyToManyField(blank=True, related_name='vendors', to='Houses.House')),
                ('occupation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Houses.Occupation')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Owners.Owner')),
            ],
        ),
    ]
