# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-06-15 08:24
from __future__ import unicode_literals

from django.db import migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0029_auto_20190615_1341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='housesearchslug',
            name='fields',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[['rent_max', 'rent_max'], ['furnish_type', 'furnish_type'], ['house_type', 'house_type'], ['accomodation_allowed', 'accomodation_allowed'], ['bhk_count', 'bhk_count'], ['shared_room_bed_count', 'shared_room_bed_count'], ['accomodation_type', 'accomodation_type'], ['latitude', 'latitude'], ['longitude', 'longitude'], ['radius', 'radius']], max_length=500),
        ),
    ]
