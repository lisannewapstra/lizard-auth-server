# -*- coding: utf-8 -*-

from appconf import AppConf
from datetime import timedelta
from django.conf import settings  # NOQA


class LizardAuthServerAppConf(AppConf):
    """Default values.

    These defaults may be overriden in the Django settings file of your
    project. In that case, don't forget to prefix them, for example:

    LIZARD_AUTH_SERVER_JWT_ALGORITHM = 'HS512'
    LIZARD_AUTH_SERVER_JWT_EXPIRATION_DELTA = timedelta(hours=12)

    """

    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_DELTA = timedelta(seconds=300)
    DIRTY_HARDCODED_PASSWORD = "dirtyhardcodedpassword"
    ACCOUNT_ACTIVATION_DAYS = 45  # A month of vacation + some margin
