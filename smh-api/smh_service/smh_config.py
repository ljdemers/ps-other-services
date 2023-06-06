import time
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from api_clients.utils import json_logger
from smh_service.clients import port_service_client_detect, ais_client

from ps_env_config import config

name = "SMH API"

logger = json_logger(__name__, level=config.get('LOG_LEVEL'), sort_keys=False)


class FlaskApp(Flask):

    def __init__(self, *args, **kwargs):
        super(FlaskApp, self).__init__(*args, **kwargs)
        code = 400
        for i in range(3):
            status, code = self.system_check()
            if code != 200:  # system failed
                logger.error(f'Try {i+1}: {status}')
                time.sleep(3)
            else:
                break
        if code != 200:
            exit(1)  # fail to connect to ports and DB - Shutdown the App

    @classmethod
    def system_check(cls):
        status = 'DB/Ports good'
        code = 200
        try:
            port_service_client_detect().check_port()
            ais_version = ais_client().system_status()["version"]
            if ais_version < '3.2.0':
                os.environ['DEFAULT_DOWNSAMPLE_FREQUENCY_SECONDS'] = '0'  # not available
        except Exception as exc:
            status = str(exc)
            # try older version
            if 'UNIMPLEMENTED' in status:
                logger.debug(config.get('PORT_SERVICE_MESSAGE_VERSION'))
                os.environ['PORT_SERVICE_MESSAGE_VERSION'] = '2.1'
            code = 424

        return status, code


app = FlaskApp(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
app.config["JSON_SORT_KEYS"] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{config.get('DB_USER')}:" \
                                        f"{config.get('DB_PASSWORD')}@" \
                                        f"{config.get('DB_HOST')}:" \
                                        f"{config.get('DB_PORT')}/{config.get('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

