# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-08 17:57
from __future__ import unicode_literals

import Homes.HomeServices.utils
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HomeServices', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MajorServiceCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('image', models.ImageField(blank=True, null=True, upload_to=Homes.HomeServices.utils.get_major_service_category_picture_upload_path)),
            ],
            options={
                'verbose_name_plural': 'Major service categories',
            },
        ),
        migrations.AlterModelOptions(
            name='servicecategory',
            options={'verbose_name_plural': 'Service categories'},
        ),
        migrations.RemoveField(
            model_name='servicecategory',
            name='is_parent',
        ),
        migrations.RemoveField(
            model_name='servicecategory',
            name='parent_category',
        ),
        migrations.AddField(
            model_name='servicecategory',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sub_categories', to='HomeServices.MajorServiceCategory'),
        ),
    ]
