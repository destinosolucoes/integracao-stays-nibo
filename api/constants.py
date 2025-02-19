from os import getenv
from dotenv import load_dotenv

load_dotenv()

STAYS_CLIENT_LOGIN = getenv("STAYS_CLIENT_LOGIN")
STAYS_CLIENT_SECRET = getenv("STAYS_CLIENT_SECRET")

DB_DRIVER = getenv("DB_DRIVER")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")
DB_NAME = getenv("DB_NAME")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")