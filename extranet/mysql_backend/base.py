"""
Backend MySQL personnalisé qui ignore la vérification de version MariaDB.
Nécessaire car le serveur distant utilise MariaDB 10.3 et Django 6 exige 10.6+.
"""
from django.db.backends.mysql import base


class DatabaseWrapper(base.DatabaseWrapper):
    def get_database_version(self):
        """Retourner une version fictive compatible pour contourner la vérification"""
        return (10, 6, 0)
