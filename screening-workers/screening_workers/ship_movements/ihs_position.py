from screening_workers.lib.utils import json_logger

from screening_workers.lib.blacklist import (
    get_port_country_severity,
)
from screening_workers.lib.ihs_ps_voyage_country_mapping \
    import IHS_PS_VOYAGE_COUNTRY_MAPPING
from screening_api.screenings.enums import Severity
from screening_workers.lib.sis_api.collections import IhsMovementCollection


class IHSPositionLogic:

    def __init__(self, portservice_client, blacklisted_ports,
                 smh_client=None, convert_ihs_data=False,
                 log_level='INFO'):
        self.portservice_client = portservice_client
        self.blacklisted_ports = blacklisted_ports
        self.smh_client = smh_client
        self.convert_ihs_data = convert_ihs_data
        self.logger = json_logger(__name__, level=log_level)

    def _get_port_data(self, field, value):
        if self.smh_client:
            response = self.smh_client.get_port_data(field=field, value=value)
            if 'port_code' in response:
                return response
            else:
                return None

        return self.portservice_client.get_port_data(field, value)

    def process_ihs_positions(self, ihs_positions, stop_date=None):
        self.logger.info('Starting to process IHS positions')

        if self.convert_ihs_data:
            # convert to object from dict
            ihs_positions = IhsMovementCollection(None).\
                decode({'objects': ihs_positions}, True)

        overall_severity = Severity.OK
        ihs_movement_data = []

        for position in ihs_positions:
            if stop_date is None or position.entered > stop_date:

                # if port and country is empty then return movement_type
                if position.port_name == '' and position.country_name == '':
                    position.port_name = position.movement_type
                    position.country_name = position.movement_type
                    port_severity = Severity.OK
                else:
                    # Get current position port severity.
                    port_severity = self.get_position_severity(
                        ihs_port_id=position.ihs_port_id,
                        port_name=position.port_name,
                        country_name=position.country_name,
                    )

                # Get current position's previous port severity.
                previous_port_severity = self.get_position_severity(
                    port_name=position.last_port_of_call_name,
                    country_code=position.last_port_of_call_country_code,
                    country_name=position.last_port_of_call_country,
                )

                # Get current position's destination port severity.
                destination_port_severity = self.get_position_severity(
                    port_name=position.destination_port,
                    country_code=None,
                )

                ihs_movement = position.ihs_movement_dict()
                # adding severity for each record
                ihs_movement['port_severity'] = str(port_severity.name)
                ihs_movement['last_port_of_call_severity'] = \
                    str(previous_port_severity.name)
                ihs_movement['destination_port_severity'] = \
                    str(destination_port_severity.name)

                ihs_movement_data.append(ihs_movement)

                overall_severity = max([
                    overall_severity,
                    port_severity,
                    previous_port_severity,
                    destination_port_severity,
                ])

        return overall_severity, ihs_movement_data

    def get_position_severity(
        self,
        ihs_port_id=None,
        port_name=None,
        country_name=None,
        country_code=None,
    ):
        """ Attempt to retrieve the severity of a position's port.

        Check for a port is set on the blacklist has a IHS Port ID.

        If there is no account specific blacklist for IHS port ID. Attempt to
        retrieve a global blacklist for the IHS port ID.

        If there is not port set in the blacklist, attempt to retrieve a
        blacklist for a specific account by port name.

        If there is not an account specific port in the blacklist attempt to
        retrieve a global port blacklist by port name.

        Depending if country_name or country_code is passed in, perform the
        following checks for the given variable.

            If there is not a port blacklist for a port name. Attempt to get an
            port blacklist by country name or alpha 2.

            If there is not a specific blacklist by country name,
            attempt to retrieve a global port blacklist by country name or
            alpha 2.

        Else return Severity.OK

        Args:
            ihs_port_id (`obj`: int, optional): An ID used to query blacklists
                for associated ports.
            port_name (`obj`: str, optional): The name of the port to query
                the blacklist with.
            country_name (`obj`: str, optional): The name of the country to
                query the blacklist with.
            country_code (`obj`: str, optional): ISO 3166 Alpha 2/3 code
                associated with a port's country. Used to query blacklist
                if country name is not supplied.

        Returns:
            Severity: The severity of the position's
                port information (previous, current, destination).
        """

        severities = list()
        severities.extend(self._get_port_specific_severities_by_ihs_port_id(
            ihs_port_id
        ))

        severities.extend(self._get_port_specific_severities_by_port_name(
            port_name
        ))

        severities.extend(self._get_country_specific_severities(
            port_name,
            country_name
        ))

        severities.extend(self._get_country_code_specific_severities(
            port_name,
            country_code
        ))

        if severities:
            severity = max(severities)
        else:
            severity = Severity.OK

        return severity

    def _get_port_specific_severities_by_ihs_port_id(
        self,
        ihs_port_id
    ):
        """ Retrieve Port specific severities if IHS Port ID is provided.

        Args:
            ihs_port_id (str): An IHS Port ID if there was one. It is possible
                it could be ``None``.

        Returns:
            list: An empty list if there were no Port Blacklists associated
                with a given ihs_port_id.
            list: Of severities associated with IHS Port ID.
        """
        severities = list()
        if ihs_port_id is not None:
            port = self._get_port_data('ihs_port_id', ihs_port_id)
            if port:
                bl_port = get_port_country_severity(self.blacklisted_ports,
                                                    port['port_name'],
                                                    port['port_country_name'])
                severities.append(bl_port.get('severity') or Severity.OK)

        return severities

    def _get_port_specific_severities_by_port_name(
        self,
        port_name
    ):
        """ Retrieve Port specific severities by Port name, if provided.

        Args:
            port_name (str): A name of a port provided by IHS.

        Returns:
            list: A list of previously obtained severities if ``port_name``
                evaluates to ``False``.
            list: An empty list if there were no Port Blacklists associated
                with a given ``port_name``.
            list: Of severities associated with the port name.
        """
        severities = list()

        if not port_name:
            return severities

        port = self._get_port_data('port_name', port_name)
        if port:
            bl_port = get_port_country_severity(self.blacklisted_ports,
                                                port['port_name'],
                                                port['port_country_name'])

            severities.append(bl_port.get('severity') or Severity.OK)

        return severities

    def _get_country_specific_severities(
        self,
        port_name,
        country_name,
        get_country_mapping=True,
    ):
        """ Retrieve Port specific severities by country name.

        Args:
            port_name (str): A name of a port provided by IHS.
            country_name (str): A name of the country associated with a port /
                position information.
            get_country_mapping (bool): Whether or not to obtain the mapping
                for the passed in ``country_name``. Defaults to ``True``.

        Returns:
            list: A list of previously obtained severities if ``country_name``
                evaluates to ``False``.
            list: An empty list if there were no Port Blacklists associated
                the mapping of the given ``country_name``.
            list: Of severities associated with the mapped ``country_name``.
        """
        severities = list()

        if not country_name:
            return severities

        mapped_country_name = country_name
        if get_country_mapping:
            mapped_country_name = IHS_PS_VOYAGE_COUNTRY_MAPPING.get(
                country_name,
                country_name
            )

        # check both original and mapped country name if different
        bl_port = get_port_country_severity(
            self.blacklisted_ports,
            port_name=port_name,
            country_name=country_name)
        severities.append(bl_port.get('severity') or Severity.OK)

        if mapped_country_name != country_name:
            bl_port = get_port_country_severity(
                self.blacklisted_ports,
                country_name=mapped_country_name)
            severities.append(bl_port.get('severity') or Severity.OK)

        return severities

    def _get_country_code_specific_severities(
        self,
        port_name,
        country_code
    ):
        """ Retrieve Port specific severities by country code.

        Args:
            port_name (str): A name of a port provided by IHS.
            country_code (str): A country's ISO 3166 Alpha 2 or Alpha 3
             representation.

        Returns:
            list: A list of previously obtained severities if
                ``country_code`` evaluates to ``False``.
            list: An empty list if there were no Port Blacklists associated
                the mapping of the given ``country_code``.
            list: Of severities associated with ``country_code``.
        """
        severities = list()

        if not country_code:
            return severities

        # 2 letter country code
        country = self._get_port_data(
            'iso_3166_1_alpha_2', country_code
        )
        if country:
            bl_port = get_port_country_severity(
                self.blacklisted_ports,
                port_name=port_name,
                country_name=country['port_country_name'])
            severities.append(bl_port.get('severity') or Severity.OK)

        # 3 letter country code
        country = self._get_port_data(
            'country_code', country_code
        )
        if country:
            bl_port = get_port_country_severity(
                self.blacklisted_ports,
                port_name=port_name,
                country_name=country['port_country_name'])
            severities.append(bl_port.get('severity') or Severity.OK)

        return severities
