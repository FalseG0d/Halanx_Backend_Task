# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-26 12:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('Notifications', '0003_auto_20171204_1846'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='category',
            field=models.CharField(blank=True, choices=[('InsufficientBalance1', 'InsufficientBalance1'),
                                                        ('InsufficientBalance2', 'InsufficientBalance2'),
                                                        ('BatchAccepted', 'BatchAccepted'),
                                                        ('BatchDelivered', 'BatchDelivered'), ('CashBack', 'CashBack'),
                                                        ('TitleAssigned', 'TitleAssigned')], max_length=50, null=True),
        ),
    ]
