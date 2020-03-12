import json

import requests
from decouple import config

from Homes.Houses.utils import SCOUT_TASK_URL
from utility.cross_project_task_utils import TASK_TYPE
from utility.logging_utils import sentry_debug_logger
from utility.render_response_utils import DATA


def send_scout_task_to_scout_backend(data, task_type):
    request_data = {
        DATA: data,
        TASK_TYPE: task_type
    }

    sentry_debug_logger.debug('sending scout task with data as ' + str(request_data))

    x = requests.post(SCOUT_TASK_URL, data=json.dumps(request_data),
                      headers={'Content-type': 'application/json'},
                      timeout=10,
                      auth=(config('SCOUT_BACKEND_ADMIN_USERNAME'), config('SCOUT_BACKEND_ADMIN_PASSWORD')))

    sentry_debug_logger.debug('status code in sending task to scout ' + str(x.status_code))
    sentry_debug_logger.debug('content is  ' + str(x.content))
