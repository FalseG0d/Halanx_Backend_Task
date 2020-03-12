# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-07-05 05:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0024_tenant_affiliate_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenantdocument',
            name='type',
            field=models.CharField(choices=[('Id', 'Id'), ('Employment', 'Employment'), ('PAN', 'PAN'), ('Electricity', 'Electricity'), ('Water', 'Water'), ('Maintenance', 'Maintenance'), ('Insurance', 'Insurance'), ('Agreement', 'Agreement'), ('Others', 'Others'), ('Aadhaar', 'Aadhaar')], max_length=30),
        ),
    ]