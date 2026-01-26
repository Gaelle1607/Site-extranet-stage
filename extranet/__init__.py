import pymysql
pymysql.version_info = (2, 2, 4, 'final', 0)
pymysql.install_as_MySQLdb()

# Monkey-patch pour contourner la vérification de version MariaDB
from django.db.backends.mysql import base as mysql_base
_original_get_database_version = mysql_base.DatabaseWrapper.get_database_version

def _patched_get_database_version(self):
    try:
        return _original_get_database_version(self)
    except Exception:
        return (10, 6, 0)

# Retourner toujours une version compatible
mysql_base.DatabaseWrapper.get_database_version = lambda self: (10, 6, 0)
