# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-10 09:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ships', '0006_auto_20190507_1029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipinspection',
            name='imo_id',
            field=models.CharField(blank=True, db_index=True, max_length=10, null=True),
        ),
    ]
