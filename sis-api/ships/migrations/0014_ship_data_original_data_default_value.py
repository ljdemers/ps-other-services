# Generated by Django 2.2.25 on 2022-05-05 11:18

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ships', '0013_association_type_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipdata',
            name='original_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True),
        ),
    ]
