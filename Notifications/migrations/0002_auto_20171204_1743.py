# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-04 12:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('Notifications', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='category',
            field=models.CharField(blank=True, choices=[('InsufficientBalance1', 'InsufficientBalance1'),
                                                        ('InsufficientBalance2', 'InsufficientBalance2'),
                                                        ('BatchAccepted', 'BatchAccepted'),
                                                        ('BatchDelivered', 'BatchDelivered')], max_length=50,
                                   null=True),
        ),
        migrations.DeleteModel(
            name='NotificationCategory',
        ),
    ]
