"""
This module only exists to execute one-time scripts.
Nothing here should be referenced in or executed any other modules.
"""
import simplejson as json
from django.core.exceptions import ObjectDoesNotExist

import database
database._import_data("__data/San Diego")

