# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-02-21 04:14
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0035_customer_fbtemplate'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='UserBase.Customer')),
            ],
        ),
    ]