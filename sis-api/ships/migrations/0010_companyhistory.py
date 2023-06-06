# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-02-02 19:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ships', '0009_flaghistory'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('imo_id', models.CharField(max_length=10)),
                ('association_type', models.CharField(blank=True, choices=[('REGISTERED', 'Registered Owner'), ('OPERATOR', 'Operator'), ('SHIP_MANAGER', 'Ship Manager'), ('TECHNICAL_MANAGER', 'Technical Manager'), ('GROUP_BENEFICIAL_OWNER', 'Group Beneficial Owner')], max_length=30, null=True, verbose_name='Association type')),
                ('company_name', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('company_code', models.IntegerField(blank=True, db_index=True, null=True)),
                ('company_registration_country', models.CharField(blank=True, max_length=255, null=True)),
                ('company_control_country', models.CharField(blank=True, max_length=255, null=True)),
                ('company_domicile_country', models.CharField(blank=True, max_length=255, null=True)),
                ('company_domicile_code', models.CharField(blank=True, max_length=3, null=True)),
                ('manual_edit', models.BooleanField(default=False)),
                ('ignore', models.BooleanField(default=False)),
                ('ship_history', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='company_history', to='ships.ShipDataHistory')),
            ],
            options={
                'verbose_name': 'company_history',
                'verbose_name_plural': 'company history',
            },
        ),
    ]
