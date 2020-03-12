#!/usr/bin/env python

import sys

from utility.environments import set_settings_module

if __name__ == "__main__":
    set_settings_module()
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
