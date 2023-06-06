import logging

from django.db import models
from django.utils import timezone

from ships.models.flag import Flag
from sis_api.utils import convert_to_float, convert_to_int

logger = logging.getLogger(__name__)


class ShipDataManager(models.Manager):
    def import_data(self, attrs, data=None):
        """Import a single ship."""
        pkname = "imo_id"
        pk = attrs[pkname]

        def parse_data(attrs):
            """Parse and format incoming attributes"""
            attrs["data"] = data
            attrs["updated"] = timezone.now()

            if "gross_tonnage" in attrs:
                attrs["gross_tonnage"] = convert_to_float(attrs["gross_tonnage"])

            if "length_overall_loa" in attrs:
                attrs["length_overall_loa"] = convert_to_float(
                    attrs["length_overall_loa"]
                )
            if "year_of_build" in attrs:
                attrs["year_of_build"] = convert_to_int(attrs["year_of_build"])

            # if none exists find_one returns None
            attrs["flag"] = Flag.objects.find_one(
                flag_name=attrs.get("flag_name", None)
            )

            return attrs

        # parsing the incoming data
        attrs = parse_data(attrs)

        # check if ship data for this pk is present
        ihs_mmsi = attrs.pop("mmsi")
        try:
            ship = self.get(**{pkname: pk})
            # udpate all attributes passed except mmsi
            [setattr(ship, k, v) for k, v in attrs.items()]
            ship.save()
        except self.model.DoesNotExist:
            ship = self.create(**attrs)

        # update mmsi
        try:
            # check the MMSI in archived records, update if the MMSI is new
            current_mmsi = self.create_or_update_mmsi_history(ship, ihs_mmsi)
        except Exception as e:
            msg = "Problem creating / updating MMSI history: {}".format(str(e))
            logger.exception(msg)
            raise

        ship.mmsi = current_mmsi
        ship.save()

        return ship.pk

    @staticmethod
    def create_or_update_mmsi_history(
        ship, ihs_mmsi, date_from=None, manual_change=False
    ):
        """Update MMSI History object"""
        from ships.models.mmsi_history import MMSIHistory

        # Check if the date_from was set, if not, just use timezone aware now()
        if date_from is None:
            date_from = timezone.now()
        # check if MMSIHistory data for this IMO is present
        # if there is no record for this MMSI, we create the first one
        if MMSIHistory.objects.filter(imo_number=ship.imo_id).count() == 0:
            # Don't create history for empty MMSI
            if ihs_mmsi is None:
                return

            logger.info("creating a new MMSIHistory record for: %s", ship.imo_id)
            # if the ship is not in the archive, create new mmsi history record
            MMSIHistory.objects.create(
                mmsi=ihs_mmsi, imo_number=ship.imo_id, effective_from=date_from
            )
            return ihs_mmsi

        if ihs_mmsi != ship.mmsi:
            # mmsi has changed
            if (
                MMSIHistory.objects.filter(
                    imo_number=ship.imo_id, mmsi=ihs_mmsi
                ).count()
                != 0
            ):
                # this is an old mmsi for the same ship
                # keep the current stored one
                return ship.mmsi

            else:
                # this is a more up-to-date mmsi, create a new history object

                # close the old one
                # Update old MMSI History object with an effective_to date.
                try:
                    old_obj = MMSIHistory.objects.filter(
                        imo_number=ship.imo_id, effective_to__isnull=True
                    )[0]
                    if old_obj.effective_from > date_from and manual_change is True:
                        # We set manually an older entry than the one we have
                        # So we have to push it back
                        old_obj.effective_from = date_from

                    old_obj.effective_to = date_from
                    old_obj.save()
                except IndexError:
                    # there is no object to close
                    pass

                # Don't create history for empty MMSI
                if ihs_mmsi is None:
                    return

                MMSIHistory.objects.create(
                    mmsi=ihs_mmsi,
                    imo_number=ship.imo_id,
                    effective_from=date_from,
                )

                return ihs_mmsi
        else:
            # mmsi has not changed
            if manual_change is True:
                # User changes effective_from date of MMSI for the ship
                mmsi_to_update = MMSIHistory.objects.get(
                    imo_number=ship.imo_id, mmsi=ihs_mmsi
                )
                mmsi_to_update.effective_from = date_from
                mmsi_to_update.save()
            return ship.mmsi
