# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-08-09 08:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0027_tenantmoveinrequest'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tenantmoveinrequest',
            name='tenant',
        ),
        migrations.DeleteModel(
            name='TenantMoveInRequest',
        ),
    ]
