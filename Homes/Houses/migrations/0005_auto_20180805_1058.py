# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-05 05:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0004_auto_20180805_1053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='houseapplication',
            name='accomodation_allowed',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('girls', 'Girls'), ('boys', 'Boys'), ('family', 'Family')], max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='houseapplication',
            name='bhk_count',
            field=models.PositiveIntegerField(blank=True, default=1, null=True),
        ),
        migrations.AlterField(
            model_name='houseapplication',
            name='current_rent',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='houseapplication',
            name='current_security_deposit',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='houseapplication',
            name='expected_rent',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='houseapplication',
            name='expected_security_deposit',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='houseapplication',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='applications', to='Owners.Owner'),
        ),
    ]
