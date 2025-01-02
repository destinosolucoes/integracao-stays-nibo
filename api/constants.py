from os import getenv
from dotenv import load_dotenv

load_dotenv()

STAYS_CLIENT_LOGIN = getenv("STAYS_CLIENT_LOGIN")
STAYS_CLIENT_SECRET = getenv("STAYS_CLIENT_SECRET")