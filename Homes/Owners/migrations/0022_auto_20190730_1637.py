# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-07-30 11:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0025_auto_20190705_1059'),
        ('Owners', '0021_ownerlisting'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownerlisting',
            name='referrer_owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owner_listings', to='Owners.Owner'),
        ),
        migrations.AddField(
            model_name='ownerlisting',
            name='referrer_tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owner_listings', to='Tenants.Tenant'),
        ),
        migrations.AddField(
            model_name='ownerlisting',
            name='source_category',
            field=models.CharField(blank=True, choices=[('Guest', 'Guest'), ('Affiliate', 'Affiliate'), ('Tenant', 'Tenant'), ('Owner', 'Owner')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='ownerlisting',
            name='source_category_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
