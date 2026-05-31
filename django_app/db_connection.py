import pymssql
from django.conf import settings


def get_connection():
    cfg = settings.MSSQL_CONFIG
    return pymssql.connect(
        server=cfg['server'],
        user=cfg['user'],
        password=cfg['password'],
        database=cfg['database'],
        port=cfg['port'],
        tds_version=cfg['tds_version'],
        charset=cfg['charset'],
    )