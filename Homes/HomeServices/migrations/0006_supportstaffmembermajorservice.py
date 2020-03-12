# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-08-16 06:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HomeServices', '0005_auto_20190808_1113'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportStaffMemberMajorService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='HomeServices.MajorServiceCategory')),
                ('staff_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='HomeServices.SupportStaffMember')),
            ],
        ),
    ]