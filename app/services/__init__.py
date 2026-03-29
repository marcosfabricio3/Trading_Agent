from .exchange import ExchangeService
from .db import DBService

# Instancias compartidas para la API y el Motor
exchange = ExchangeService()
db = DBService()
