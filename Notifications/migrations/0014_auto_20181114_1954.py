# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-11-14 14:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Notifications', '0013_notification_seen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='category',
            field=models.CharField(blank=True, choices=[('InsufficientBalance1', 'InsufficientBalance1'), ('InsufficientBalance2', 'InsufficientBalance2'), ('BatchAccepted', 'BatchAccepted'), ('BatchDelivered', 'BatchDelivered'), ('OrderDelivered', 'OrderDelivered'), ('CashBack', 'CashBack'), ('TitleAssigned', 'TitleAssigned'), ('Alert', 'Alert'), ('Announcement', 'Announcement'), ('NewMessage', 'NewMessage'), ('PlaceVisit', 'PlaceVisit'), ('MonthlyRentRequest', 'MonthlyRentRequest'), ('MoveInChargesRequest', 'MoveInChargesRequest'), ('CashCollectConfirmation', 'CashCollectConfirmation')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='notificationimage',
            name='category',
            field=models.CharField(blank=True, choices=[('InsufficientBalance1', 'InsufficientBalance1'), ('InsufficientBalance2', 'InsufficientBalance2'), ('BatchAccepted', 'BatchAccepted'), ('BatchDelivered', 'BatchDelivered'), ('OrderDelivered', 'OrderDelivered'), ('CashBack', 'CashBack'), ('TitleAssigned', 'TitleAssigned'), ('Alert', 'Alert'), ('Announcement', 'Announcement'), ('NewMessage', 'NewMessage'), ('PlaceVisit', 'PlaceVisit'), ('MonthlyRentRequest', 'MonthlyRentRequest'), ('MoveInChargesRequest', 'MoveInChargesRequest'), ('CashCollectConfirmation', 'CashCollectConfirmation')], max_length=50, null=True),
        ),
    ]
