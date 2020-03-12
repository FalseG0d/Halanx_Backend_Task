# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-03-27 17:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Bookings', '0020_auto_20190315_1610'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExistingTenantOnboarding',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rent', models.FloatField(blank=True, null=True)),
                ('security_deposit', models.FloatField(blank=True, null=True)),
                ('original_license_start_date', models.DateTimeField(blank=True, null=True)),
                ('security_deposit_held_by_owner', models.BooleanField(default=True)),
                ('last_monthly_rent_paid_on', models.DateTimeField(blank=True, null=True)),
                ('last_monthly_rent_paid_to_owner', models.BooleanField(default=True)),
            ],
        ),
        migrations.AddField(
            model_name='booking',
            name='type',
            field=models.CharField(choices=[('new_tenant_booking', 'New Tenant Booking'), ('existing_tenant_booking', 'Existing Tenant Booking')], default='new_tenant_booking', max_length=50),
        ),
        migrations.AddField(
            model_name='existingtenantonboarding',
            name='booking',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='onboarding', to='Bookings.Booking'),
        ),
    ]