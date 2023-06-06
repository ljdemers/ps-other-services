import logging
from decimal import Decimal

import dateutil
import pytz
import ujson
from django.db import models

logger = logging.getLogger(__name__)


class ShipMovementManager(models.Manager):

    IHS_TO_SIS_MAPPING = {
        "ArrivalDate": "arrival_date",
        "ArrivalDateFull": "timestamp",
        "CallID": "ihs_id",
        "Country": "country_name",
        "DateCreated": "ihs_creation_date",
        "Destination": "destination_port",
        "ETA": "estimated_time_of_arrival",
        "HoursinPort": "hours_in_port",
        "LRNOIMOShipNo": "imo_id",
        "LastPortofCallArrivalDate": "last_port_of_call_arrival_date",
        "LastPortofCallCode": "last_port_of_call_code",
        "LastPortofCallCountry": "last_port_of_call_country",
        "LastPortofCallCountryCode": "last_port_of_call_country_code",
        "LastPortofCallName": "last_port_of_call_name",
        "LastPortofCallSailDate": "last_port_of_call_sail_date",
        "Movementtype": "movement_type",
        "Port": "port_name",
        "PortGeoID": "ihs_port_geo_id",
        "PortID": "ihs_port_id",
        "PortLatitudeDecimal": "latitude",
        "PortLongitudeDecimal": "longitude",
        "SailDate": "sail_date",
        "SailDateFull": "sail_date_full",
        "ShipName": "ship_name",
        "ShipType": "ship_type",
    }

    def import_data(self, attrs, data=None):
        """
        Take a dictionary representing ShipMovement fields, clean and
        validate datetime and decimal fields and call the `get_or_create`
        method to insert object into the database

        :param attrs: Dictionary of ShipMovement fields
        :param data: Unused param to keep compatibility with ships.tasks
        :return: ShipMovement object
        """
        if "creation_date" in attrs:
            # Delete attr that the task appends
            del attrs["creation_date"]

        cleaned_attrs = {}
        for ihs_key, sis_key in list(self.IHS_TO_SIS_MAPPING.items()):
            value = attrs.pop(ihs_key, None)

            if value == "":
                value = None

            if ihs_key in ["latitude", "longitude"] and value >= 971:
                value = None

            cleaned_attrs[sis_key] = value

        cleaned_attrs = self._update_datetime_objects_in_attrs(cleaned_attrs)
        cleaned_attrs = self._update_decimal_objects_in_attrs(cleaned_attrs)
        cleaned_attrs["extra_data"] = ujson.dumps(attrs)

        obj, created = self.get_or_create(
            imo_id=cleaned_attrs.pop("imo_id"),
            ihs_id=cleaned_attrs.pop("ihs_id"),
            timestamp=cleaned_attrs.pop("timestamp"),
            defaults=cleaned_attrs,
        )
        if not created:
            for key, value in list(cleaned_attrs.items()):
                setattr(obj, key, value)
            obj.save()

        return obj

    def _update_datetime_objects_in_attrs(self, attrs):
        """
        Conver the following datetime fields into UTC aware datetime objects
            * `timestamp`
            * `estimated_time_of_arrival`
            * `ihs_creation_date`
            * `last_port_of_call_arrival_date`
            * `last_port_of_call_sail_date`
            * `sail_date_full`,

        :param attrs: Dictionary of ShipMovement fields
        :return: Dictionary of updated key / value pairs
        """
        datetime_keys = [
            "timestamp",
            "estimated_time_of_arrival",
            "ihs_creation_date",
            "last_port_of_call_arrival_date",
            "last_port_of_call_sail_date",
            "sail_date_full",
        ]

        new_datetime_items = dict(
            [
                (key, self._make_datetime_string_timezone_aware(attrs.get(key)))
                for key in datetime_keys
            ]
        )

        attrs.update(new_datetime_items)
        return attrs

    @staticmethod
    def _make_datetime_string_timezone_aware(datetime_string):
        """
        Convert a datetime string to a datetime object that is UTC TZ aware.
        If the datetime object if set to year 9999 then it is invalid and we
        will throw it away

        :param datetime_string: A string representing a date / time or None
        :return: Datetime object that is UTC timezone aware or None
        """
        datetime_obj = None

        if datetime_string:
            datetime_obj = dateutil.parser.parse(datetime_string)
            if datetime_obj.year == 9999:
                datetime_obj = None
            elif not datetime_obj.tzinfo:
                datetime_obj = pytz.utc.localize(datetime_obj)

        return datetime_obj

    def _update_decimal_objects_in_attrs(self, attrs):
        """
        Loop through the fields that are required to be decimal objects and
        convert them to Decimal objects with 6 digit precision.

        Specifically the fields:
            * `longitude`
            * `latitude`

        :param attrs: Dictionary of ShipMovement fields
        :return: Dictionary of updated key / value pairs
        """
        decimal_keys = ["longitude", "latitude"]
        new_decimal_items = dict(
            [
                (key, self._convert_string_to_decimal(attrs.get(key), key))
                for key in decimal_keys
            ]
        )

        attrs.update(new_decimal_items)
        return attrs

    @staticmethod
    def _convert_string_to_decimal(decimal_string, key):
        """
        Take a string representing a float / decimal and convert it to a
        Decimal object with 6 digit precision.

        :param decimal_string: String represeting a float / decimal
        :return: Decimal object / None
        """
        is_latitude = "latitude" in key
        if decimal_string:
            decimal = Decimal(decimal_string).quantize(Decimal(".000001"))

            if is_latitude and decimal > Decimal("90.0") or decimal < Decimal("-90.0"):
                decimal = None

            elif (
                not is_latitude
                and decimal > Decimal("180.0")
                or decimal < Decimal("-180.0")
            ):
                decimal = None

        else:
            decimal = None

        return decimal
