# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-14 07:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0006_tenant_favorite_houses'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='referral_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='tenant',
            name='referrer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='referrals', to='Tenants.Tenant'),
        ),
    ]
