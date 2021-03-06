# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-10-22 17:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Bookings', '0005_auto_20180808_2244'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingFacility',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='FacilityItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('type', models.CharField(blank=True, choices=[('sub_unit', 'Sub Unit'), ('common_area', 'Common Area')], max_length=15, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='booking',
            name='lock_in_period',
            field=models.IntegerField(blank=True, default=6, null=True),
        ),
        migrations.AddField(
            model_name='bookingfacility',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Bookings.FacilityItem'),
        ),
        migrations.AddField(
            model_name='booking',
            name='facilities',
            field=models.ManyToManyField(blank=True, null=True, to='Bookings.BookingFacility'),
        ),
    ]
