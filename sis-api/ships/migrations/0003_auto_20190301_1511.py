# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-01 15:11
from __future__ import unicode_literals
from django.conf import settings
import ujson

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


def json_migrate_forward(app, schema_editor):
    ship_data_model = app.get_model("ships", "ShipData")
    for ship in ship_data_model.objects.all().iterator():
        if isinstance(ship.data, str):
            # That's the scenario that should happen
            ship.data = ujson.loads(ship.data)
            ship.save()
        elif isinstance(ship.data, dict):
            # Unlikely we have already some pure JSONS
            # That's the scenario that should happen
            pass
        else:
            raise TypeError("The data was supposed to be json in str or"
                            " dict, but it was {}".format(ship.data))


def json_migrate_backwards(app, schema_editor):
    ship_data_model = app.get_model("ships", "ShipData")
    for ship in ship_data_model.objects.all().iterator():
        # Check if the db has the data in JSON
        if isinstance(ship.data, dict):
            ship.data = ujson.dumps(ship.data)
        # If the data is already json in a string, just pass it
        elif isinstance(ship.data, str):
            pass

        ship.save()


class Migration(migrations.Migration):

    dependencies = [
        ('ships', '0002_MMSI_history'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mmsihistory',
            name='effective_to',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='shipdata',
            name='data',
            field=django.contrib.postgres.fields.jsonb.JSONField(),
        ),
        migrations.RunPython(json_migrate_forward, json_migrate_backwards),
        migrations.CreateModel(
            name='ShipDataManualChange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('changed_ship', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to="ships.ShipData")),
                ('changed_data',
                 django.contrib.postgres.fields.jsonb.JSONField()),
                ('date_of_change', models.DateTimeField(auto_now_add=True)),
                ('user',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                   to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
