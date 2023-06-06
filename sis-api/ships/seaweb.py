"""Translation into canonical attribute names"""

# This map contains exceptions to the general translate logic for CSV attributes
# (without underscores). If there are any cases where the general logic fails,
# they should be added to this map
csv_attribute_map = {
    "LRNO": "imo_id",
    "LRIMOShipNo": "imo_id",
    "LRNOIMOShipNo": "imo_id",
    "MaritimeMobileServiceIdentityMMSINumber": "mmsi",
    "Flag": "flag_name",
    "Country": "country_name",
    "Port": "port_name",
    "Class": "shipclass",
    # Inconsistent capitalisation
    'DOCCOEB': 'doc_coeb',
    'SBTPLSBTProtectedLocation': 'sbt_pl_sbt_protected_location',
    'PhotoPresent': 'photo_present',
    "PandIClub": "pandi_club",
    "PandIClubCode": "pandi_club_code",
    "Shipname": "ship_name",
    'Destination': 'destination_port',
    "DateCreated": "ihs_creation_date",
    "CallID": "ihs_id",
    "Movementtype": 'movement_type',
    "PortGeoID": "ihs_port_geo_id",
    "PortID": "ihs_port_id",
    'ETA': 'estimated_time_of_arrival',
    'PortLatitudeDecimal': 'latitude',
    'PortLongitudeDecimal': 'longitude',
    'ArrivalDateFull': 'timestamp',
}

# This map contains exceptions to the logic for XML attributes (with underscores)
# These are mainly those where Polestar names differ from the ones provided by SeaWeb
xml_attribute_map = {
    "LRNO": "imo_id",
    "LR_IMO_Ship_No": "imo_id",
    "Maritime_Mobile_Service_Identity_MMSI_Number": "mmsi",
    "Flag": "flag_name",
    "Country": "country_name",
    "Port": "port_name",
    "Class": "shipclass",

    # Inconsistent units
    'TEU_Capacity_14_t_Homogenous': 'teu_capacity_14t_homogeneous',
}

misspellings = {
    'coutry': 'country',
    'auxilary': 'auxiliary',
    'lenght': 'length',
    'docmicile': 'domicile',
    'homogenous': 'homogeneous'
}


def translate(attrname):
    """
    Inspects a mixed-case attribute name and returns a consistent one with underscores separating words
    Also corrects some misspellings in the attribute names.
    """
    if '_' in attrname:
        # Look for places where we want to adjust the underscoring or rename the attribute entirely
        if attrname in xml_attribute_map:
            return xml_attribute_map.get(attrname).lower()
        words = attrname.lower().split('_')
    else:
        # Exceptions to the general rule.
        if attrname in csv_attribute_map:
            return csv_attribute_map.get(attrname).lower()
        result = []
        for i, c in enumerate(attrname):
            if c.isupper():
                # Sometimes the CSV files contain prepositions that haven't been CapWorded to mark them
                # as separate words. This tries to find if the previous word ends in a preposition and
                # retroactively changes the preposition into a separate word.
                if i > 2 and attrname[i - 2: i] in ('of', 'to', 'in', 'or', 'by'):
                    # Some exceptions to the previous rule where the last part of a normal word looks like
                    # a preposition
                    if attrname[i - 3] != 'a' and (attrname[i - 3: i] != 'tor'):  # "main" "operator"
                        result[-2:] = ['_' + attrname[i - 2: i]]
                elif i > 3 and attrname[i - 3: i] == 'out':
                    result[-3:] = ['_out']
                # Detect word breaks by looking at changes from lowercase to uppercase
                if i and ((attrname[i - 1].islower()) or
                          # or from uppercase to lowercase, in which case the last uppercase letter is
                          # part of the next word
                          (i < len(attrname) - 1 and (attrname[i + 1].islower()))):
                    result.append('_')
            # Sequences of digits begin new words
            if i and c.isdigit() and not attrname[i - 1].isdigit():
                result.append('_')
            result.append(c)
        # Join up the character strings and then split them into words for the spell check
        words = ''.join(result).lower().split('_')

    words = [misspellings.get(word, word) for word in words if word]
    return '_'.join(words)
