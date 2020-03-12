# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-10-29 10:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0013_house_agreement_commencement_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='HouseFurnishingBill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('gst', models.FloatField()),
                ('cleared', models.BooleanField(default=False)),
                ('house', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='Houses.House')),
            ],
        ),
        migrations.CreateModel(
            name='HouseFurnishingItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=250)),
                ('price', models.FloatField()),
                ('bill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='Houses.HouseFurnishingBill')),
            ],
        ),
    ]
