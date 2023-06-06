# -*- coding: utf-8 -*-
import os


def load_ini_settings(ini_file, settings_object, extra_conf_mapping=None):
    """ Set configuration INI file as attr on Django settings object.

    Args:
        ini_file (object): Path object referencing the INI file.
        settings_object (object): Django settings object.
        extra_conf_mapping (:obj:`dict`, optional): Conf to be added to the
            settings.
    """
    from configparser import ConfigParser

    if extra_conf_mapping is not None:
        CONFIG_FILE_MAPPING.update(extra_conf_mapping)

    if os.getenv("DJANGO_CONFIG_FILE", ""):
        ini_file = os.getenv("DJANGO_CONFIG_FILE")

    config = ConfigParser()
    read_files = config.read(str(ini_file))

    if read_files:
        for config_name in config.options("application"):
            value = config.get("application", config_name)
            if config_name in CONFIG_FILE_MAPPING:
                set_function, param = CONFIG_FILE_MAPPING[config_name]
                set_function(settings_object, value, param)
            else:
                config_name = config_name.upper()
                setattr(settings_object, config_name, value)


def set_doubled_list(settings_object, val, conf_name):
    """
    Args:
        settings_object (object): Django settings module.
        val (str): Value to be formatted
        conf_name (str): Name of the configuration to be set.
    """
    setattr(settings_object, conf_name, [(x, x) for x in val.split(",")])


def set_bool(settings_object, val, conf_name):
    setattr(settings_object, conf_name, val.lower() == "true")


def set_dict_value(settings_object, val, dict_item):
    if len(dict_item) == 2:
        getattr(settings_object, dict_item[0])[dict_item[1]] = val
    elif len(dict_item) == 3:
        getattr(settings_object, dict_item[0])[dict_item[1]][dict_item[2]] = \
            val


def set_value(settings_object, val, conf_name):
    setattr(settings_object, conf_name, val)


# If your config mapping is absent from the list but present in the ini it will
# assume that it should call globals()[name.upper()] = value, with the name
# value in the ini
CONFIG_FILE_MAPPING = {
    'admins': (set_doubled_list, "ADMINS"),
    'db_user': (set_dict_value, ("DATABASES", "default", "USER")),
    'db_password': (set_dict_value, ("DATABASES", "default", "PASSWORD")),
    'db_host': (set_dict_value, ("DATABASES", "default", "HOST")),
    'db_engine': (set_dict_value, ("DATABASES", "default", "ENGINE")),
    'db_name': (set_dict_value, ("DATABASES", "default", "NAME")),
    'debug': (set_bool, "DEBUG"),
    'template_debug': (set_bool, "TEMPLATE_DEBUG"),
    'tastypie_full_debug': (set_bool, "TASTYPIE_FULL_DEBUG"),
    'allowed_hosts': (set_value, "ALLOWED_HOSTS"),
}
