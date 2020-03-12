# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-08-09 07:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Tenants', '0026_tenantmoveoutrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantMoveInRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timing', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movein_requests', to='Tenants.Tenant')),
            ],
        ),
    ]