import logging

import os
import watchtower
import boto3
from Halanx.settings.production import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
from Halanx.settings.development import INTERNET_ENABLED, ENVIRONMENT
from utility.environments import DEVELOPMENT

boto3_session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                              region_name=AWS_DEFAULT_REGION)

logging.basicConfig(level=logging.INFO)

cwlogger = logging.getLogger('Cloudwatch-Logger')

if os.environ.get('ENVIRONMENT') in [DEVELOPMENT, None] and not INTERNET_ENABLED:  # By default environment is
    # development in case value of enviromnet variable is None
    pass
else:
    cwlogger.addHandler(watchtower.CloudWatchLogHandler(boto3_session=boto3_session))

sentry_debug_logger = logging.getLogger('sentry_debug_logger')
