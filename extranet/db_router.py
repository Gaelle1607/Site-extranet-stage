class DatabaseRouter:
    """
    Router pour diriger les requêtes vers la bonne base de données.
    - Tables distantes (comcli, comclilig, catalogue, prod) -> 'logigvd'
    - Autres tables (utilisateurs, commandes, etc.) -> 'default'
    """

    # Modèles qui utilisent la base distante logigvd
    logigvd_models = {'comcli', 'comclilig', 'catalogue', 'prod'}

    def db_for_read(self, model, **hints):
        if model._meta.db_table in self.logigvd_models:
            return 'logigvd'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.db_table in self.logigvd_models:
            return 'logigvd'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Autorise les relations entre objets de la même base
        db1 = self._get_db(obj1)
        db2 = self._get_db(obj2)
        if db1 and db2:
            return db1 == db2
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Les tables distantes ne doivent pas être migrées
        if model_name and model_name.lower() in self.logigvd_models:
            return False
        # Les autres tables vont dans default
        return db == 'default'

    def _get_db(self, obj):
        if obj._meta.db_table in self.logigvd_models:
            return 'logigvd'
        return 'default'
