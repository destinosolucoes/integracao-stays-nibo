"""API package initialization"""

# Import consolidated modules
from .stays.all import *
from .nibo.all import *

# Import core modules that we'll keep
from .constants import *
from .utils import *
from .queue import *
from .webhook_processor import *

# Export all for ease of import
__all__ = [
    'constants',
    'utils',
    'queue',
    'webhook_processor',
    'stays',
    'nibo',
]

import pymysql
pymysql.install_as_MySQLdb()