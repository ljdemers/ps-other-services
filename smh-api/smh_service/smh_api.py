import json
import time
from datetime import datetime
import threading
import traceback

from flask import jsonify, request
from flask_cors import cross_origin
from flask_httpauth import HTTPBasicAuth
from webargs.flaskparser import use_args
from werkzeug.security import generate_password_hash, check_password_hash

from api_clients.utils import json_logger, str2date
from smh_service.smh import get_ports
from smh_service.clients import port_service_client
from smh_service import __version__
from smh_service.smh_api_schema import SMHSchema, DEFAULT_EEZ_REGION_STATUS
from smh_service.smh_task import SMHTask, stats
from smh_service.models import SMHUsers
from smh_service.smh_config import app, db

from ps_env_config import config

name = "SMH API"

logger = json_logger(__name__, level=config.get('LOG_LEVEL'), sort_keys=False)

smh_schema = SMHSchema()
users = {}
auth = HTTPBasicAuth()

with app.app_context():
    for user in db.session.query(SMHUsers).all():
        if hasattr(user, 'username'):
            users[user.username] = generate_password_hash(user.password)


@auth.verify_password
def verify_password(username, password):
    if username in users:
        login = check_password_hash(users.get(username), password)
        try:
            if login:
                SMHUsers().update_user_request_count(username)
            return login
        except Exception as exc:
            logger.error("Login failed:", exception=exc)

    return False


@app.route('/')
@app.route('/api/v1/system/status')
@cross_origin()  # allow all origins all methods.
def index(secure='', code=200):
    resp_dict = dict({'msg': f"SMH Service{secure}"})
    resp_dict['client_ip'] = request.remote_addr
    resp_dict['version'] = __version__
    resp_dict['route'] = request.path
    resp_dict['status_code'] = code
    resp_dict['use_aisapi'] = config.get('USE_AISAPI')
    resp_dict['default_downsample_frequency'] = config.get('DEFAULT_DOWNSAMPLE_FREQUENCY_SECONDS')
    resp_dict['port_message_version'] = \
        config.get('PORT_SERVICE_MESSAGE_VERSION')
    resp = jsonify(resp_dict)
    resp.status_code = code
    return resp


@app.route('/secure', methods=['GET'])
@auth.login_required
def secure_page():
    # testing a secure area for User login
    user = auth.username()
    return index(f' - Secure (user: {user})')


@app.route('/system/status')
@cross_origin()  # allow all origins all methods.
def system():
    # Check DB and ports API
    status, code = app.system_check()
    return index(f' - {status}', code=code)


@app.errorhandler(404)
def page_not_found(error):
    logger.error('Page not found: %s' % request.path)
    return index(f' - Not found {error}', 404)


@app.errorhandler(401)
def unauthorized_access(error):
    user = auth.username()
    logger.error('Unauthorized Access: %s' % request.path)
    return index(f' - Unauthorized Access ({user}) {error}', 401)


@app.errorhandler(500)
def internal_server_error(error):
    logger.error('Server Error: %s' % error)
    return index(f' - Server Error {error}', 500)


@app.errorhandler(504)
def gateway_timeout(error):
    logger.error('Gateway Time-out: %s' % error)
    return index(f' - Gateway Time-out {error}', 504)


@app.errorhandler(Exception)
def unhandled_exception(e):
    logger.error('Unhandled Exception: %s' % str(e))
    return index(" - " + str(e), 500)


@app.route('/exception')
def exception():
    # test exception handling
    raise Exception('THIS IS AN EXCEPTION!')


@app.route('/api/v1/portdata/', methods=['GET'])
@cross_origin()
@auth.login_required
def get_port_data():
    field = request.args.get('field')
    value = request.args.get('value')

    if value is None or field is None:
        resp_dict = {'error': 'Invalid inputs'}
    else:
        resp_dict = port_service_client().get_port_data(field, value)
    if not resp_dict:
        resp_dict = {'error': 'Not found'}
    resp_dict['version'] = __version__
    resp_dict['user'] = auth.username()
    resp_dict['field'] = field
    resp_dict['data'] = value
    resp = jsonify(resp_dict)
    resp.status_code = 200
    return resp


@app.route('/api/v1/portcalls/', methods=['GET'])
@cross_origin()
@auth.login_required
def get_port_calls():
    """
       API method to detect port (from ports API) or EEZ (from a DB table)
       Returns:
           A List - Detected Port/EEZ/Regions appended to each positions or exception
    """

    #  positions (list): List of positions to detect ports/EEZ for
    #  table (str, optional): EEZ table to use or None to use Ports API
    try:
        positions = json.loads(request.args.get('positions', '[]'))
        table = request.args.get('table')
        eez_field = request.args.get('eez_field', 'eez_')
        eez_status = request.args.get('eez_status', DEFAULT_EEZ_REGION_STATUS)
        if not positions or not isinstance(positions, list):
            raise TypeError
    except Exception:
        return index(f' - Invalid Inputs', code=400)

    resp_port = get_ports(positions, table, eez_field, eez_status)
    resp_dict = dict({'version': __version__, 'port_calls': resp_port})
    resp_dict['user'] = auth.username()
    resp = jsonify(resp_dict)
    resp.status_code = 200
    return resp


@app.route('/api/v1/shipmovementhistory/<imo_number>', methods=['GET'])
@cross_origin()
@auth.login_required
@stats.timer('smh_total_elapsed')
@use_args(smh_schema)
def get_ship_movement_history(args, imo_number):
    smh_datetime = datetime.utcnow()
    end_date = request.args.get('end_date')
    request_days = int(request.args.get('request_days') or 0)
    ais_days = 60  # if no end_date is passed
    try:  # if days passed
        ais_days = int(end_date)
        end_date = None
    except (TypeError, ValueError):
        #  i.e date is passed - process it later
        # format: YYYY-MM-DDTHH:mm:ssXXXXX
        if end_date and len(end_date) >= 19:
            end_date = end_date[:19]
            ais_days = (smh_datetime - str2date(end_date)).days

    if request_days and ais_days < request_days:
        ais_days = request_days
    request_days = request_days or ais_days

    # dict of options either default, computed or request params
    for key, value in request.args.items():
        args[key] = value

    options = smh_schema.dump({
        **args,
        **dict(
            ais_days=ais_days,
            request_days=int(request_days),
            version=__version__,
            user=auth.username(),
            use_aisapi=config.get('USE_AISAPI') == 'True'
        )
    })

    # process the request in SMH task
    smh_task = SMHTask(imo_number, options)
    try:
        last_smh, cached_positions = smh_task.get_cached_smh(end_date)  # read/process cached SMH
        smh_task.get_smh_results(last_smh, cached_positions)  # get new SMH results
        smh_task.update_cache(last_smh)  # update cache with new/updated SMH results
        start = time.monotonic()
        response = smh_task.prepare_response()
        smh_task.options['response_creation_elapsed'] = round(time.monotonic() - start, 3)

        # Save/cache in DB (in another thread i.e response is not blocked)
        if smh_task.options.get('cache_updated', 0) == 1:
            thread = threading.Thread(target=smh_task.cache_results, args=(app, ))
            thread.start()
        else:
            logger.info("SMH completed: No new Visit or Position")
    except Exception as exc:
        error = str(exc)
        logger.error("Exception", Exception_in_SMH=error, imo_number=imo_number,
                     trace=traceback.print_exc())
        stats.incr('smh_exception')  # exceptions in SMH
        return index(" - " + error, 424)

    return response


if __name__ == '__main__':
    logger.info("Starting service")
    app.run(host="0.0.0.0", port=8080, threaded=True)
