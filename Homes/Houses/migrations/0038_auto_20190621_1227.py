# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-06-21 06:57
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0033_remove_tenant_added_by'),
        ('Houses', '0037_auto_20190621_1221'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='billsplit',
            unique_together=set([('bill', 'tenant')]),
        ),
    ]
