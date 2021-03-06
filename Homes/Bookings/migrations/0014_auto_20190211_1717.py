# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-11 11:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('Houses', '0024_auto_20190206_2031'),
        ('Tenants', '0021_auto_20181220_2144'),
        ('Bookings', '0013_monthlyrent_cancelled'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvanceBooking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expected_rent', models.FloatField(blank=True, null=True)),
                ('expected_movein_date', models.DateField(blank=True, null=True)),
                ('accomodation_for', multiselectfield.db.fields.MultiSelectField(choices=[('girls', 'Girls'), ('boys', 'Boys'), ('family', 'Family')], max_length=25)),
                ('space_type', models.CharField(choices=[('shared', 'Shared rooms'), ('private', 'Private rooms'), ('flat', 'Entire house')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now_add=True)),
                ('cancelled', models.BooleanField(default=False)),
                ('space_subtype', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='advance_bookings', to='Houses.SpaceSubType')),
                ('tenant', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='advance_bookings', to='Tenants.Tenant')),
            ],
        ),
        migrations.RenameField(
            model_name='booking',
            old_name='created',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='booking',
            old_name='modified',
            new_name='modified_at',
        ),
    ]
