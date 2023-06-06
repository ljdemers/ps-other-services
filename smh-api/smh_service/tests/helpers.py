def ais_position_item(timestamp="2019-12-28T21:50:49", latitude=35.029917, longitude=136.850783,
                      status=None):
    position = {"latitude": latitude, "longitude": longitude, "timestamp": timestamp,
                "source": "OT", 'status': status}

    return position


def ihs_item(timestamp="2019-12-26T21:50:49", sail_date_full="2020-01-06T11:56:12",
             port_name="Nagoya", latitude=35.029917, longitude=136.850783, type=None):
    ihs = {"latitude": latitude, "longitude": longitude,
           "movement_type": "", "port_name": port_name, "country_name": "Japan",
           "sail_date_full": sail_date_full,
           "ship_name": "BLUE CAT", "ship_type": "Bulk Carrier",
           "timestamp": timestamp}
    if type:
        ihs["type"] = type

    return ihs


def gap_item(current_report_timestamp=None, current_report_gps=(0, 0),
             last_report_timestamp='2020-06-04T12:56:40Z',
             last_report_gps=(29.915585, -93.889038),
             gap_hours=532.368):
    gap = {'current_report': None if not current_report_timestamp else
    {'timestamp': current_report_timestamp, 'latitude': current_report_gps[0],
     'longitude': current_report_gps[1], },
           'current_report_timestamp': current_report_timestamp,
           'gap_hours': gap_hours,
           'last_report': {'latitude': last_report_gps[0], 'longitude': last_report_gps[1],
                           'timestamp': last_report_timestamp},
           'last_report_timestamp': last_report_timestamp}

    return gap


def smh_data(id=1, timestamp=None, imo_number='123', port_calls=None, visits=None,
             positions=None, ihs=None,
             options=None, update_count=None):
    if not options:
        options = {}
    options['read_db_elapsed'] = 1
    options['timestamp'] = timestamp
    options['id'] = id
    if update_count:
        options['update_count'] = update_count

    gap = []
    eez_visits = []
    return options, visits or {}, positions or {}, ihs or [], gap, eez_visits


def visit_data(entered="2020-07-29T18:27:35Z", departed=None, speed=None,
               latitude=52.099998, longitude=4.266667, port=None, type='IHS'):
    visit = {'entered': entered, 'departed': departed, 'speed': speed,
             'latitude': latitude, 'longitude': longitude, 'type': type,
             'port': port or {}
             }

    return visit
