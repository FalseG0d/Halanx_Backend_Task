# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-19 15:54
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('UserBase', '0049_auto_20180410_1831'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpamReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('verified', models.BooleanField(default=False)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spam_reports',
                                               to='UserBase.Customer')),
                ('reporter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                               related_name='spams_reported', to='UserBase.Customer')),
            ],
        ),
    ]
