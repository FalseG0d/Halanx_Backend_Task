# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-10 17:28
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models

import UserBase.models


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0037_auto_20180308_1316'),
    ]

    operations = [
        migrations.CreateModel(
            name='Picture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to=UserBase.models.get_picture_upload_path)),
                ('isProfilePic', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RenameField(
            model_name='customer',
            old_name='FbTemplate',
            new_name='fbTemplate',
        ),
        migrations.AddField(
            model_name='picture',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pictures',
                                    to='UserBase.Customer'),
        ),
    ]