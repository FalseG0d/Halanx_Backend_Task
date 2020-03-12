# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-06-15 07:15
from __future__ import unicode_literals

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0027_auto_20190613_1634'),
    ]

    operations = [
        migrations.CreateModel(
            name='HouseSearchSlug',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(max_length=500)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('accomodation_allowed', multiselectfield.db.fields.MultiSelectField(choices=[('girls', 'Girls'), ('boys', 'Boys'), ('family', 'Family')], max_length=25)),
                ('accomodation_type', multiselectfield.db.fields.MultiSelectField(choices=[('shared', 'Shared rooms'), ('private', 'Private rooms'), ('flat', 'Entire house')], max_length=25)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]