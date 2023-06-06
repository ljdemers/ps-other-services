# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-07 10:29
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ships', '0005_auto_20190402_1521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipdata',
            name='original_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True),
        ),
        migrations.AlterField(
            model_name='shipinspection',
            name='detained',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='shipinspection',
            name='dwt',
            field=models.IntegerField(blank=True, help_text='Deadweight tonnage', null=True),
        ),
        migrations.AlterField(
            model_name='shipinspection',
            name='expanded_inspection',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='shipinspection',
            name='gt',
            field=models.IntegerField(blank=True, help_text='Gross tonnage', null=True),
        ),
        migrations.AlterField(
            model_name='shipinspection',
            name='no_days_detained',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='shipinspection',
            name='no_defects',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='shipinspection',
            name='number_part_days_detained',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='shipinspection',
            name='yob',
            field=models.SmallIntegerField(blank=True, help_text='Year of build', null=True),
        ),
    ]
