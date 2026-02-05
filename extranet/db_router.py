"""
=============================================================================
DB_ROUTER.PY - Routeur de base de données multi-bases
=============================================================================

Ce routeur permet à Django de gérer deux bases de données simultanément :

1. Base 'default' (SQLite locale) :
   - Utilisateurs de l'extranet
   - Commandes passées via l'extranet
   - Historiques et logs
   - Sessions utilisateur

2. Base 'logigvd' (MariaDB distante) :
   - Catalogue des produits (table 'catalogue')
   - Informations produits (table 'prod')
   - Clients existants (table 'comcli')
   - Lignes de commande existantes (table 'comclilig')

Le routeur intercepte chaque requête et la dirige vers la bonne base
en fonction du modèle Django utilisé.

Projet : Extranet Giffaud Groupe
=============================================================================
"""


class DatabaseRouter:
    """
    Routeur de base de données pour l'architecture multi-bases.

    Ce routeur analyse chaque opération de base de données (lecture, écriture,
    migration) et détermine quelle base utiliser selon le modèle concerné.

    Attributs:
        logigvd_models (set): Ensemble des noms de tables stockées dans la base distante
    """

    # Tables stockées dans la base de données distante LogiGVD
    # Ces tables correspondent au système de gestion existant
    logigvd_models = {'comcli', 'comclilig', 'catalogue', 'prod'}

    def db_for_read(self, model, **hints):
        """
        Détermine la base de données à utiliser pour les opérations de lecture.

        Args:
            model: Le modèle Django concerné par la requête
            **hints: Indices supplémentaires fournis par Django

        Returns:
            str: 'logigvd' si le modèle est dans la base distante, 'default' sinon
        """
        if model._meta.db_table in self.logigvd_models:
            return 'logigvd'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Détermine la base de données à utiliser pour les opérations d'écriture.

        Args:
            model: Le modèle Django concerné par la requête
            **hints: Indices supplémentaires fournis par Django

        Returns:
            str: 'logigvd' si le modèle est dans la base distante, 'default' sinon

        Note:
            Les écritures dans la base logigvd doivent être évitées car elle
            contient des données du système existant.
        """
        if model._meta.db_table in self.logigvd_models:
            return 'logigvd'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Détermine si une relation entre deux objets est autorisée.

        Django ne permet pas les relations entre objets de bases différentes.
        Cette méthode vérifie que les deux objets sont dans la même base.

        Args:
            obj1: Premier objet de la relation
            obj2: Second objet de la relation
            **hints: Indices supplémentaires fournis par Django

        Returns:
            bool: True si les objets sont dans la même base, None sinon
        """
        db1 = self._get_db(obj1)
        db2 = self._get_db(obj2)
        if db1 and db2:
            return db1 == db2
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Contrôle les migrations de base de données.

        Les tables de la base distante logigvd ne doivent jamais être migrées
        car elles sont gérées par le système existant. Seules les tables
        de la base default sont migrées.

        Args:
            db: La base de données cible de la migration
            app_label: Le label de l'application Django
            model_name: Le nom du modèle (optionnel)
            **hints: Indices supplémentaires fournis par Django

        Returns:
            bool: False pour les modèles logigvd, True si db=='default'
        """
        # Empêche la migration des tables distantes
        if model_name and model_name.lower() in self.logigvd_models:
            return False
        # Autorise les migrations uniquement sur la base default
        return db == 'default'

    def _get_db(self, obj):
        """
        Méthode utilitaire pour déterminer la base d'un objet.

        Args:
            obj: L'objet Django dont on veut connaître la base

        Returns:
            str: Le nom de la base de données ('logigvd' ou 'default')
        """
        if obj._meta.db_table in self.logigvd_models:
            return 'logigvd'
        return 'default'
