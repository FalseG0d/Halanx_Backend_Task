# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-06 15:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0023_auto_20190205_2331'),
    ]

    operations = [
        migrations.AddField(
            model_name='house',
            name='rent_included_expenses',
            field=models.ManyToManyField(related_name='rent_excluded_houses', to='Houses.MonthlyExpenseCategory'),
        ),
        migrations.AlterField(
            model_name='housemonthlyexpense',
            name='amount',
            field=models.FloatField(blank=True, null=True),
        ),
    ]