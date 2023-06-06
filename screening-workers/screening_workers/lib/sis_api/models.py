import json
from booby import Model, fields
from screening_workers.lib.utils import str2date, DATE_FORMAT, date2str


class Flag(Model):
    iso_3166_1_alpha_2 = fields.String()
    name = fields.String()

    def __repr__(self):
        return 'Flag({}/{})'.format(self.iso_3166_1_alpha_2, self.name)

    @classmethod
    def parse(cls, raw):
        # ships resource returns str instead of dict
        if isinstance(raw, str):
            raw = json.loads(raw)

        valid_fields = ['iso_3166_1_alpha_2', 'name']

        return dict(
            (key, value)
            for key, value in raw.items()
            if key in valid_fields
        )


class Ship(Model):
    imo_id = fields.String()
    shiptype_level_5 = fields.String()
    ship_name = fields.String()
    mmsi = fields.String()
    flag = fields.Embedded(Flag, required=False)

    country_name = fields.String()
    country_id = fields.String()
    country_effective_date = fields.Integer()
    call_sign = fields.String()
    status = fields.String()
    port_of_registry = fields.String()
    classification_society = fields.String()
    deadweight = fields.Integer()
    breadth = fields.Float()
    displacement = fields.Integer()
    draught = fields.Float()
    build_country_name = fields.String()
    build_year = fields.Integer()
    shipbuilder = fields.String()
    pandi_club = fields.String()
    weight = fields.Integer()
    length = fields.Float()
    safety_management_certificate_doc_company = fields.String()
    safety_management_certificate_date_issued = fields.String()

    registered_owner = fields.String()
    registered_owner_code = fields.String()
    registered_owner_country_of_domicile = fields.String()
    registered_owner_country_of_control = fields.String()
    registered_owner_country_of_registration = fields.String()

    operator = fields.String()
    operator_company_code = fields.String()
    operator_country_of_domicile_name = fields.String()
    operator_country_of_control = fields.String()
    operator_country_of_registration = fields.String()

    group_beneficial_owner = fields.String()
    group_beneficial_owner_company_code = fields.String()
    group_beneficial_owner_country_of_domicile = fields.String()
    group_beneficial_owner_country_of_control = fields.String()
    group_beneficial_owner_country_of_registration = fields.String()

    ship_manager = fields.String()
    ship_manager_company_code = fields.String()
    ship_manager_country_of_domicile_name = fields.String()
    ship_manager_country_of_control = fields.String()
    ship_manager_country_of_registration = fields.String()

    technical_manager = fields.String()
    technical_manager_code = fields.String()
    technical_manager_country_of_domicile = fields.String()
    technical_manager_country_of_control = fields.String()
    technical_manager_country_of_registration = fields.String()

    def __repr__(self):
        return 'Ship({}/{})'.format(self.imo_id, self.ship_name)

    @classmethod
    def parse(cls, raw):
        flag_raw = raw.get('flag') or {
            'iso_3166_1_alpha_2': None,
            'name': None,
        }
        flag_data = Flag.parse(flag_raw)
        flag = Flag(**flag_data)
        return {
            'imo_id': raw['imo_id'],
            'shiptype_level_5': raw['shiptype_level_5'],
            'ship_name': raw['ship_name'],
            'mmsi': raw.get('mmsi'),
            'flag': flag,
            'country_id': flag.iso_3166_1_alpha_2,
            'country_name': flag.name,
            'country_effective_date': int(raw.get('flag_effective_date',
                                                  1900)),

            'call_sign': raw.get('call_sign'),
            'status': raw.get('ship_status'),
            'port_of_registry': raw.get('port_of_registry'),
            'classification_society': raw.get('classification_society'),
            'deadweight': int(raw.get('deadweight', 0)),
            'breadth': float(raw.get('breadth', 0)),
            'displacement': int(raw.get('displacement', 0)),
            'draught': float(raw.get('draught', 0)),
            'build_country_name': raw.get('country_of_build'),
            'build_year': int(raw.get('year_of_build', 1900)),
            'shipbuilder': raw.get('shipbuilder'),
            'pandi_club': raw.get('pandi_club'),
            'weight': int(raw.get('gross_tonnage', 0)),
            'length': float(raw.get('length_overall_loa', 0)),

            'safety_management_certificate_doc_company':
                raw.get('safety_management_certificate_doc_company'),
            'safety_management_certificate_date_issued':
                raw.get('safety_management_certificate_date_issued'),

            'registered_owner':
                raw.get('registered_owner'),
            'registered_owner_code':
                raw.get('registered_owner_code'),
            'registered_owner_country_of_domicile':
                raw.get('registered_owner_country_of_domicile'),
            'registered_owner_country_of_control':
                raw.get('registered_owner_country_of_control'),
            'registered_owner_country_of_registration':
                raw.get('registered_owner_country_of_registration'),

            'operator':
                raw.get('operator'),
            'operator_company_code':
                raw.get('operator_company_code'),
            'operator_country_of_domicile_name':
                raw.get('operator_country_of_domicile_name'),
            'operator_country_of_control':
                raw.get('operator_country_of_control'),
            'operator_country_of_registration':
                raw.get('operator_country_of_registration'),

            'group_beneficial_owner':
                raw.get('group_beneficial_owner'),
            'group_beneficial_owner_company_code':
                raw.get('group_beneficial_owner_company_code'),
            'group_beneficial_owner_country_of_domicile':
                raw.get('group_beneficial_owner_country_of_domicile'),
            'group_beneficial_owner_country_of_control':
                raw.get('group_beneficial_owner_country_of_control'),
            'group_beneficial_owner_country_of_registration':
                raw.get('group_beneficial_owner_country_of_registration'),

            'ship_manager':
                raw.get('ship_manager'),
            'ship_manager_company_code':
                raw.get('ship_manager_company_code'),
            'ship_manager_country_of_domicile_name':
                raw.get('ship_manager_country_of_domicile_name'),
            'ship_manager_country_of_control':
                raw.get('ship_manager_country_of_control'),
            'ship_manager_country_of_registration':
                raw.get('ship_manager_country_of_registration'),

            'technical_manager':
                raw.get('technical_manager'),
            'technical_manager_code':
                raw.get('technical_manager_code'),
            'technical_manager_country_of_domicile':
                raw.get('technical_manager_country_of_domicile'),
            'technical_manager_country_of_control':
                raw.get('technical_manager_country_of_control'),
            'technical_manager_country_of_registration':
                raw.get('technical_manager_country_of_registration'),
        }


class ShipInspection(Model):
    authorisation = fields.String()
    detained = fields.Boolean()
    inspection_id = fields.String()
    inspection_date = fields.String()
    number_part_days_detained = fields.Float()  # Float from SIS
    no_defects = fields.Integer()
    port_name = fields.String()
    country_name = fields.String()

    def __repr__(self):
        return 'ShipInspection({0})'.format(self.inspection_id)

    @classmethod
    def parse(cls, raw):
        number_part_days_detained = raw['number_part_days_detained']
        no_defects = raw['no_defects']
        detained = raw['detained']
        inspection_date = str2date(
            raw['inspection_date'], date_formats=DATE_FORMAT)

        if number_part_days_detained is not None:
            number_part_days_detained = float(number_part_days_detained)

        if no_defects is not None:
            no_defects = int(no_defects)

        return {
            'inspection_id': raw['inspection_id'],
            'inspection_date': inspection_date,
            'authorisation': raw['authorisation'],
            'detained': detained,
            'number_part_days_detained': number_part_days_detained,
            'no_defects': no_defects,
            'port_name': raw['port_name'],
            'country_name': raw['country_name'],
        }


class IhsMovement(Model):
    ihs_id = fields.String()
    ihs_port_id = fields.String()
    entered = fields.String()
    departed = fields.String()
    port_name = fields.String()
    country_name = fields.String()
    last_port_of_call_country = fields.String()
    last_port_of_call_name = fields.String()
    last_port_of_call_country_code = fields.String()
    latitude = fields.Float()
    longitude = fields.Float()
    destination_port = fields.String()
    movement_type = fields.String()

    def __repr__(self):
        return 'IhsMovement({0} --> {2}, {3} --> {1})'. \
            format(self.entered, self.departed,
                   self.port_name, self.country_name)

    @classmethod
    def parse(cls, raw):
        entered = str2date(raw['timestamp'])
        departed = str2date(raw.get('sail_date_full'))

        return {
            'ihs_id': raw.get('ihs_id'),
            'ihs_port_id': raw.get('ihs_port_id'),
            'entered': entered,
            'departed': departed,
            'port_name': raw.get('port_name', ''),
            'country_name': raw.get('country_name', ''),
            'last_port_of_call_country': raw.get('last_port_of_call_country'),
            'last_port_of_call_name': raw.get('last_port_of_call_name'),
            'last_port_of_call_country_code':
                raw.get('last_port_of_call_country_code'),
            'destination_port': raw.get('destination_port'),
            'latitude': float(raw.get('latitude') or 91),
            'longitude': float(raw.get('longitude') or 181),
            'movement_type': raw.get('movement_type', '')
        }

    def position_dict(self):
        return {
            'timestamp': date2str(self.entered),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'sail_date_full': date2str(self.departed)
        }

    def ihs_movement_dict(self):
        return {
            'entered': date2str(self.entered),
            'port_name': self.port_name,
            'country_name': self.country_name,
            'last_port_of_call_country': self.last_port_of_call_country,
            'last_port_of_call_name': self.last_port_of_call_name,
            'last_port_of_call_country_code':
                self.last_port_of_call_country_code,
            'destination_port': self.destination_port,
            'departed': date2str(self.departed)
        }
