from marshmallow import Schema, fields
from datetime import datetime

from ps_env_config import config

from smh_service.smh import NON_PORT_STOPS_RATE

DEFAULT_EEZ_REGION_STATUS = '1'


class SMHSchema(Schema):
    ais_gap_hours = fields.Integer(default=3)
    ais_last_midnight = fields.Integer(default=0)

    # The AIS rate at which to do AIS reporting gap detection - disabled by default
    ais_gap_rate = fields.Integer(default=0)

    # The AIS rate at which to do EEZ/region detection - disabled by default
    eez_rate = fields.Integer(default=0)
    eez_table = fields.String()
    eez_field = fields.String()

    # to join with port calls, default: 0(no)
    eez_join = fields.Integer(default=0)

    # CSV list like '1,2,3'
    eez_status = fields.String(default=DEFAULT_EEZ_REGION_STATUS)

    port_filter = fields.String()
    port_count_limit = fields.Integer(default=0)

    external_id = fields.String()
    ais_rate = fields.Integer(default=3600)

    request_days = fields.Integer(default=0)
    end_date = fields.String()
    speed_filter = fields.Integer(default=99)

    auto_config = fields.Integer(default=3)
    ihs_join = fields.Integer(default=1)
    use_cache = fields.Integer(default=1)
    overwrite_cache = fields.Boolean(default=True)
    remove_outliers = fields.Integer(default=1)
    response_type = fields.Integer(default=1)
    check_for_ihs_updates = fields.Integer(default=1)  # 0, 1, 2

    use_new_cache_table = fields.Boolean(default=True)
    save_port_visits = fields.Boolean(default=False)
    use_cached_positions = fields.Boolean(default=False)
    max_items_per_object = fields.Integer(default=None)
    zip_data = fields.Boolean(default=False)
    detect_stops = fields.Integer(default=0)
    non_port_stops_rate = fields.Integer(default=NON_PORT_STOPS_RATE)
    downsample_frequency_seconds = fields.Integer(
        default=int(config.get('DEFAULT_DOWNSAMPLE_FREQUENCY_SECONDS')))
    simple_smh = fields.Boolean(default=False)

    # @FIXME
    # Move this stuff somewhere else
    limit = fields.Integer(default=500)
    user = fields.String()
    version = fields.String()
    ais_days = fields.Integer(default=60)
    use_aisapi = fields.Boolean(default=True)


class SMHDataDictMiscDataSubschema(Schema):
    mmsi_history = fields.List(fields.Dict())
    ship_status = fields.Dict()
    static_and_voyage = fields.Dict()
    elapsed = fields.Dict()
    lengths = fields.Dict()
    non_port_stops = fields.List(fields.Dict())


class SMHDataDictSchema(Schema):

    timestamp = fields.DateTime(default=datetime.utcnow)
    imo_number = fields.String()
    cached_days = fields.Integer(default=0)
    options = fields.Dict()
    port_visits = fields.Dict()
    positions = fields.Dict()
    ais_gaps = fields.List(fields.Dict())
    eez_visits = fields.List(fields.Dict())
    ihs_movements = fields.List(fields.Dict())
    misc_data = fields.Nested(SMHDataDictMiscDataSubschema)
