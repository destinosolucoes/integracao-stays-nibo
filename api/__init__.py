"""API package initialization"""

from .index import app

import pymysql
pymysql.install_as_MySQLdb()