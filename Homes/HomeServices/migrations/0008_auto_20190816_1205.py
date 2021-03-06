# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-08-16 06:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HomeServices', '0007_auto_20190816_1159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supportstaffmembermajorservice',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_services', to='HomeServices.MajorServiceCategory'),
        ),
        migrations.AlterField(
            model_name='supportstaffmembermajorservice',
            name='staff_member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_services', to='HomeServices.SupportStaffMember'),
        ),
    ]
