# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-02-01 22:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ships', '0008_auto_20220131_1329'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlagHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('imo_id', models.CharField(max_length=10)),
                ('flag_name', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('flag_effective_date', models.CharField(blank=True, max_length=10, null=True)),
                ('manual_edit', models.BooleanField(default=False)),
                ('ignore', models.BooleanField(default=False)),
                ('ship_history', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='flag_history', to='ships.ShipDataHistory')),
            ],
            options={
                'verbose_name': 'flag_history',
                'verbose_name_plural': 'flag history',
            },
        ),
    ]
