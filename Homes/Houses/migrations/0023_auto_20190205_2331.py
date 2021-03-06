# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-05 18:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0022_housevisit_created_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='HouseMonthlyExpense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.FloatField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='house_monthly_expenses', to='Houses.MonthlyExpenseCategory')),
                ('house', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='monthly_expenses', to='Houses.House')),
            ],
        ),
        migrations.RemoveField(
            model_name='spacemonthlyexpense',
            name='category',
        ),
        migrations.RemoveField(
            model_name='spacemonthlyexpense',
            name='house',
        ),
        migrations.RemoveField(
            model_name='spacemonthlyexpense',
            name='space_subtype',
        ),
        migrations.AlterModelOptions(
            name='housevisit',
            options={'ordering': ('-scheduled_visit_time',)},
        ),
        migrations.DeleteModel(
            name='SpaceMonthlyExpense',
        ),
    ]
