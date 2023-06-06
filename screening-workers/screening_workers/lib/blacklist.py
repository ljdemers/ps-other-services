from screening_api.screenings.enums import Severity

# Temp. list for now
default_blacklisted_ports = [
    {'port': None, 'country': 'North Korea', 'country_code': 'PRK',
     'severity': Severity.CRITICAL, 'category': ''},
    {'port': None, 'country': 'Korea, North', 'country_code': 'PRK',
     'severity': Severity.CRITICAL, 'category': ''},
    {'port': None, 'country': 'Iran', 'country_code': 'IRN',
     'severity': Severity.WARNING, 'category': ''},
    {'port': None, 'country': 'Syrian Arab Republic', 'country_code': 'SYR',
     'severity': Severity.WARNING, 'category': ''},
    {'port': None, 'country': 'Cuba', 'country_code': 'CUB',
     'severity': Severity.WARNING, 'category': ''},

    {'port': 'YEVPATORIYA', 'country': None, 'severity': Severity.WARNING,
     'category': 'US and EU Sanctions - Crimea'},
    {'port': 'Theodosia', 'country':  None, 'severity': Severity.WARNING,
     'category': 'US and EU Sanctions - Crimea'},
    {'port': 'Sevastopol', 'country':  None, 'severity': Severity.WARNING,
     'category': 'US and EU Sanctions - Crimea'},
    {'port': 'Kerch', 'country':  None, 'severity': Severity.WARNING,
     'category': 'US and EU Sanctions - Crimea'},
    {'port': 'Yalta', 'country':  None, 'severity': Severity.WARNING,
     'category': 'US and EU Sanctions - Crimea'},

]


def get_port_country_severity(blacklisted_ports,
                              port_name=None,
                              country_name=None) -> dict:
    """
         SCREEN-891:
         When the Country is blacklisted, all Ports belonging to that
         Country will also be blacklisted.
    """
    found_bl_port = {}
    for bp in blacklisted_ports:
        if bp['port'] is None:
            if country_name == bp['country']:
                found_bl_port = bp
        elif bp['country'] is None:
            if port_name == bp['port']:
                found_bl_port = bp
        else:
            if port_name == bp['port'] and \
              country_name == bp['country']:
                found_bl_port = bp
                break

    return found_bl_port
