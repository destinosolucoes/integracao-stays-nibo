"""API package initialization"""

from .constants import *
from .utils import *
from .queue import *
from .webhook_processor import *

# Import submodules
from .stays import index as stays
from .nibo import index as nibo
from .nibo import transaction as nibo_transaction
from .nibo import operational as nibo_operational
from .nibo import comission as nibo_comission
from .nibo import receivables as nibo_receivables

# Export all for ease of import
__all__ = [
    'stays',
    'nibo',
    'nibo_transaction',
    'nibo_operational',
    'nibo_comission',
    'nibo_receivables',
]

import pymysql
pymysql.install_as_MySQLdb()