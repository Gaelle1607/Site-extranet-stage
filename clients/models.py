"""
==============================================================================
                    EXTRANET GIFFAUD GROUPE - Application Clients
                              Fichier: models.py
==============================================================================

Description:
    Ce fichier définit les modèles de données pour la gestion des utilisateurs
    et clients de l'application Extranet Giffaud Groupe. Il gère :
    - Les comptes utilisateurs liés aux clients du système de gestion
    - Les demandes de réinitialisation de mot de passe
    - Les tokens sécurisés pour la réinitialisation par email
    - L'historique des suppressions d'utilisateurs
    - La gestion temporaire des utilisateurs supprimés (corbeille)

Auteur: Giffaud Groupe
Date de création: 2024
Dernière modification: 2025

Dépendances:
    - Django ORM pour la gestion des modèles
    - Base de données distante 'logigvd' pour les informations clients
==============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import secrets


class Utilisateur(models.Model):
    """
    Modèle représentant un utilisateur de l'extranet.

    Ce modèle étend le modèle User de Django en ajoutant une liaison
    avec le système de gestion commercial via le code_tiers.
    Chaque utilisateur de l'extranet est associé à un client dans
    la base de données distante (logigvd).

    Attributes:
        user (OneToOneField): Relation vers le modèle User Django.
            Permet d'hériter de l'authentification Django standard.
        code_tiers (str): Identifiant unique du client dans le système
            de gestion commercial. Utilisé pour récupérer les informations
            client depuis la table 'comcli' de la base distante.

    Relations:
        - user: Lien OneToOne vers django.contrib.auth.models.User
        - demandes_mdp: Lien inverse vers DemandeMotDePasse

    Example:
        >>> utilisateur = Utilisateur.objects.get(user__username='client001')
        >>> print(utilisateur.code_tiers)
        'CLTIERS001'
        >>> client = utilisateur.get_client_distant()
        >>> print(client.nom)
        'ENTREPRISE DUPONT'
    """

    # Liaison vers le modèle User Django standard
    # CASCADE: si l'utilisateur Django est supprimé, le profil Utilisateur l'est aussi
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='utilisateur'
    )

    # Code tiers pour lier à la table comcli de la base de données distante
    # Ce code est l'identifiant unique du client dans le système de gestion
    code_tiers = models.CharField('Code tiers', max_length=50)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        """
        Représentation textuelle de l'utilisateur.

        Returns:
            str: Format "username - code_tiers"
        """
        return f"{self.user.username} - {self.code_tiers}"

    def get_client_distant(self):
        """
        Récupère les informations du client depuis la base de données distante.

        Cette méthode exécute une requête SQL directe sur la base 'logigvd'
        pour récupérer les informations du client associé au code_tiers.
        Elle privilégie les entrées sans complément d'adresse pour obtenir
        l'adresse principale du client.

        La requête utilise un ORDER BY pour garantir des résultats cohérents
        et déterministes en cas de doublons.

        Returns:
            SimpleNamespace: Objet avec les attributs nom, complement,
                adresse, cp, acheminement. Retourne None si aucun client
                n'est trouvé pour ce code_tiers.

        Note:
            Utilise une connexion directe via Django's database routing
            vers la base 'logigvd'.

        Example:
            >>> client = utilisateur.get_client_distant()
            >>> if client:
            ...     print(f"{client.nom}, {client.cp} {client.acheminement}")
            'ENTREPRISE DUPONT, 44000 NANTES'
        """
        from django.db import connections
        from types import SimpleNamespace

        with connections['logigvd'].cursor() as cursor:
            # Première requête: chercher une entrée avec complement vide
            # (adresse principale du client)
            cursor.execute("""
                SELECT nom, complement, adresse, cp, acheminement FROM comcli
                WHERE tiers = %s AND (complement IS NULL OR TRIM(complement) = '')
                ORDER BY nom
                LIMIT 1
            """, [self.code_tiers])
            row = cursor.fetchone()

            # Si aucune entrée sans complément, prendre la première entrée disponible
            if not row:
                cursor.execute("""
                    SELECT nom, complement, adresse, cp, acheminement FROM comcli
                    WHERE tiers = %s ORDER BY complement, nom LIMIT 1
                """, [self.code_tiers])
                row = cursor.fetchone()

        # Construire et retourner l'objet SimpleNamespace avec les données
        if row:
            return SimpleNamespace(
                nom=row[0],
                complement=row[1],
                adresse=row[2],
                cp=row[3],
                acheminement=row[4]
            )
        return None


class DemandeMotDePasse(models.Model):
    """
    Modèle pour les demandes de réinitialisation de mot de passe.

    Ce modèle permet de tracer les demandes faites par les utilisateurs
    qui ont oublié leur mot de passe. Un administrateur peut consulter
    ces demandes et les traiter manuellement si nécessaire.

    Workflow:
        1. L'utilisateur fait une demande de réinitialisation
        2. Une entrée est créée avec traitee=False
        3. L'administrateur voit la demande dans le tableau de bord
        4. Après traitement, traitee passe à True avec date_traitement

    Attributes:
        utilisateur (ForeignKey): Référence vers l'utilisateur demandeur.
        date_demande (DateTimeField): Date/heure de la demande (auto).
        traitee (BooleanField): Indique si la demande a été traitée.
        date_traitement (DateTimeField): Date/heure du traitement.

    Example:
        >>> demande = DemandeMotDePasse.objects.create(utilisateur=user)
        >>> # Plus tard, après traitement:
        >>> demande.traitee = True
        >>> demande.date_traitement = timezone.now()
        >>> demande.save()
    """

    # Lien vers l'utilisateur qui a fait la demande
    # CASCADE: si l'utilisateur est supprimé, ses demandes le sont aussi
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='demandes_mdp',
        verbose_name='Utilisateur'
    )

    # Date de création de la demande (remplie automatiquement)
    date_demande = models.DateTimeField('Date de demande', auto_now_add=True)

    # Statut de traitement de la demande
    traitee = models.BooleanField('Traitée', default=False)

    # Date à laquelle la demande a été traitée (optionnel)
    date_traitement = models.DateTimeField(
        'Date de traitement',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Demande de mot de passe'
        verbose_name_plural = 'Demandes de mot de passe'
        # Tri par date décroissante: les plus récentes en premier
        ordering = ['-date_demande']

    def __str__(self):
        """
        Représentation textuelle de la demande.

        Returns:
            str: Format "Demande de username - DD/MM/YYYY HH:MM"
        """
        return f"Demande de {self.utilisateur.user.username} - {self.date_demande.strftime('%d/%m/%Y %H:%M')}"


class TokenResetPassword(models.Model):
    """
    Modèle pour les tokens de réinitialisation de mot de passe par email.

    Ce modèle gère les tokens sécurisés envoyés par email aux utilisateurs
    pour leur permettre de réinitialiser leur mot de passe de manière
    autonome, sans intervention d'un administrateur.

    Sécurité:
        - Token généré avec secrets.token_hex (64 caractères hexadécimaux)
        - Validité limitée à 1 heure
        - Utilisation unique (marqué comme utilisé après usage)
        - Les anciens tokens non utilisés sont invalidés à la génération

    Attributes:
        user (ForeignKey): Référence vers l'utilisateur Django.
        token (str): Token unique de 64 caractères hexadécimaux.
        date_creation (DateTimeField): Date/heure de création (auto).
        utilise (BooleanField): Indique si le token a été utilisé.

    Example:
        >>> # Générer un token pour un utilisateur
        >>> token_obj = TokenResetPassword.generer_token(user)
        >>> # Vérifier la validité
        >>> if token_obj.est_valide():
        ...     # Procéder à la réinitialisation
        ...     pass
    """

    # Lien vers l'utilisateur Django (pas Utilisateur car les admins n'ont pas de profil)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reset_tokens',
        verbose_name='Utilisateur'
    )

    # Token unique de 64 caractères hexadécimaux
    # Généré avec secrets.token_hex(32) = 64 caractères
    token = models.CharField('Token', max_length=64, unique=True)

    # Date de création du token (pour vérifier l'expiration)
    date_creation = models.DateTimeField('Date de création', auto_now_add=True)

    # Indique si le token a déjà été utilisé
    utilise = models.BooleanField('Utilisé', default=False)

    class Meta:
        verbose_name = 'Token de réinitialisation'
        verbose_name_plural = 'Tokens de réinitialisation'
        ordering = ['-date_creation']

    def __str__(self):
        """
        Représentation textuelle du token.

        Returns:
            str: Format "Token pour username - DD/MM/YYYY HH:MM"
        """
        return f"Token pour {self.user.username} - {self.date_creation.strftime('%d/%m/%Y %H:%M')}"

    @classmethod
    def generer_token(cls, user):
        """
        Génère un nouveau token de réinitialisation pour un utilisateur.

        Cette méthode crée un nouveau token sécurisé et invalide tous
        les tokens précédents non utilisés de cet utilisateur pour
        éviter les conflits et renforcer la sécurité.

        Args:
            user (User): L'utilisateur Django pour lequel générer le token.

        Returns:
            TokenResetPassword: Le nouveau token créé.

        Note:
            Utilise secrets.token_hex pour générer un token cryptographiquement
            sécurisé. Le format hexadécimal évite les problèmes d'encodage
            dans les URLs et les emails.

        Example:
            >>> token_obj = TokenResetPassword.generer_token(user)
            >>> print(len(token_obj.token))  # 64 caractères
            64
        """
        # Invalider tous les anciens tokens non utilisés de cet utilisateur
        # Cela empêche l'utilisation de vieux liens de réinitialisation
        cls.objects.filter(user=user, utilise=False).update(utilise=True)

        # Créer un nouveau token hexadécimal de 64 caractères
        # token_hex(32) génère 32 octets = 64 caractères hexadécimaux
        token = secrets.token_hex(32)

        return cls.objects.create(user=user, token=token)

    def est_valide(self):
        """
        Vérifie si le token est encore valide.

        Un token est valide si:
        - Il n'a pas encore été utilisé
        - Il a été créé il y a moins d'1 heure

        Returns:
            bool: True si le token peut être utilisé, False sinon.

        Example:
            >>> if token_obj.est_valide():
            ...     # Le token peut être utilisé
            ...     pass
        """
        # Un token déjà utilisé n'est plus valide
        if self.utilise:
            return False

        # Calculer la date limite de validité (1 heure après création)
        limite = self.date_creation + timedelta(hours=1)

        # Le token est valide si on est avant la date limite
        return timezone.now() < limite

    @classmethod
    def nettoyer_anciens(cls):
        """
        Supprime les tokens de plus de 24 heures.

        Cette méthode de maintenance doit être appelée périodiquement
        (par exemple via une tâche cron ou un management command)
        pour nettoyer les tokens expirés et libérer de l'espace.

        Note:
            Les tokens de plus de 24h sont supprimés même s'ils n'ont
            jamais été utilisés.

        Example:
            >>> TokenResetPassword.nettoyer_anciens()  # Appelé par cron
        """
        # Calculer la date limite (24 heures dans le passé)
        limite = timezone.now() - timedelta(hours=24)

        # Supprimer tous les tokens créés avant cette limite
        cls.objects.filter(date_creation__lt=limite).delete()


class HistoriqueSuppressionUtilisateur(models.Model):
    """
    Modèle pour l'historique des utilisateurs supprimés définitivement.

    Ce modèle conserve une trace des utilisateurs qui ont été supprimés
    après expiration du délai de restauration (5 minutes). Il permet
    d'avoir un audit des suppressions pour des raisons légales ou
    de traçabilité.

    Workflow:
        1. Un utilisateur est supprimé -> UtilisateurSupprime créé
        2. Après 5 minutes sans restauration
        3. HistoriqueSuppressionUtilisateur créé avec les infos minimales
        4. UtilisateurSupprime supprimé définitivement

    Attributes:
        username (str): Nom d'utilisateur du compte supprimé.
        nom_client (str): Nom commercial du client.
        code_tiers (str): Code tiers dans le système de gestion.
        nb_commandes (int): Nombre de commandes passées par ce client.
        date_suppression_definitive (DateTimeField): Date de suppression.

    Note:
        Ce modèle ne contient que des informations minimales pour
        la traçabilité. Aucune donnée sensible n'est conservée.
    """

    # Informations de base de l'utilisateur supprimé
    username = models.CharField('Nom d\'utilisateur', max_length=150)
    nom_client = models.CharField('Nom du client', max_length=200)
    code_tiers = models.CharField('Code tiers', max_length=50)

    # Statistiques pour référence
    nb_commandes = models.PositiveIntegerField('Nombre de commandes', default=0)

    # Date de la suppression définitive (automatique)
    date_suppression_definitive = models.DateTimeField(
        'Date de suppression définitive',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Historique de suppression utilisateur'
        verbose_name_plural = 'Historiques de suppression utilisateurs'
        ordering = ['-date_suppression_definitive']

    def __str__(self):
        """
        Représentation textuelle de l'historique.

        Returns:
            str: Format "Suppression définitive username - nom_client"
        """
        return f"Suppression définitive {self.username} - {self.nom_client}"


class UtilisateurSupprime(models.Model):
    """
    Modèle pour les utilisateurs supprimés temporairement (corbeille).

    Ce modèle implémente une fonctionnalité de "corbeille" permettant
    de restaurer un utilisateur supprimé pendant une période de 5 minutes.
    Après ce délai, l'utilisateur et ses données sont définitivement
    supprimés.

    Cette fonctionnalité protège contre les suppressions accidentelles
    en permettant à l'administrateur d'annuler son action.

    Workflow:
        1. Admin supprime un utilisateur
        2. Les données sont copiées dans UtilisateurSupprime
        3. L'utilisateur original est supprimé de User/Utilisateur
        4. Pendant 5 minutes, l'admin peut restaurer l'utilisateur
        5. Après 5 minutes, nettoyer_anciens() supprime définitivement

    Attributes:
        username (str): Nom d'utilisateur original.
        password_hash (str): Hash du mot de passe pour restauration.
        email (str): Adresse email de l'utilisateur.
        first_name (str): Prénom de l'utilisateur.
        last_name (str): Nom de famille de l'utilisateur.
        date_joined (DateTimeField): Date d'inscription originale.
        code_tiers (str): Code tiers du client.
        nom_client (str): Nom commercial du client.
        commandes_json (JSONField): Liste des commandes au format JSON.
        date_suppression (DateTimeField): Date de la suppression.

    Example:
        >>> # Vérifier si restaurable
        >>> if utilisateur_supprime.est_restaurable():
        ...     # Restaurer l'utilisateur
        ...     pass
        >>> # Temps restant avant suppression définitive
        >>> print(f"Temps restant: {utilisateur_supprime.temps_restant()} secondes")
    """

    # Données de l'utilisateur original (pour restauration)
    username = models.CharField('Nom d\'utilisateur', max_length=150)
    password_hash = models.CharField('Mot de passe hashé', max_length=128)
    email = models.EmailField('Email', blank=True, default='')
    first_name = models.CharField('Prénom', max_length=150, blank=True, default='')
    last_name = models.CharField('Nom', max_length=150, blank=True, default='')
    date_joined = models.DateTimeField('Date d\'inscription')

    # Données métier
    code_tiers = models.CharField('Code tiers', max_length=50)
    nom_client = models.CharField('Nom du client', max_length=200, blank=True, default='')

    # Commandes stockées en JSON pour préserver les données
    # Format: [{"numero": "CMD001", "date": "2024-01-01", ...}, ...]
    commandes_json = models.JSONField('Commandes', default=list)

    # Date de la suppression (pour calcul du délai de restauration)
    date_suppression = models.DateTimeField('Date de suppression', auto_now_add=True)

    class Meta:
        verbose_name = 'Utilisateur supprimé'
        verbose_name_plural = 'Utilisateurs supprimés'
        ordering = ['-date_suppression']

    def __str__(self):
        """
        Représentation textuelle de l'utilisateur supprimé.

        Returns:
            str: Format "Utilisateur supprimé username"
        """
        return f"Utilisateur supprimé {self.username}"

    def est_restaurable(self):
        """
        Vérifie si l'utilisateur peut encore être restauré.

        La restauration est possible pendant 5 minutes après la
        suppression. Passé ce délai, les données seront définitivement
        supprimées par la méthode nettoyer_anciens().

        Returns:
            bool: True si la restauration est encore possible.

        Example:
            >>> if utilisateur_supprime.est_restaurable():
            ...     print("Restauration possible!")
        """
        # Calculer la date limite de restauration (5 minutes après suppression)
        limite = self.date_suppression + timedelta(minutes=5)

        # Restaurable si on est avant la limite
        return timezone.now() < limite

    def temps_restant(self):
        """
        Calcule le temps restant avant suppression définitive.

        Cette méthode est utile pour afficher un compte à rebours
        dans l'interface d'administration.

        Returns:
            int: Nombre de secondes restantes avant suppression définitive.
                Retourne 0 si le délai est dépassé.

        Example:
            >>> secondes = utilisateur_supprime.temps_restant()
            >>> minutes = secondes // 60
            >>> print(f"Il reste {minutes} minutes pour restaurer")
        """
        # Calculer la date limite
        limite = self.date_suppression + timedelta(minutes=5)

        # Calculer le delta entre maintenant et la limite
        delta = limite - timezone.now()

        # Retourner le nombre de secondes (minimum 0)
        return max(0, int(delta.total_seconds()))

    @classmethod
    def nettoyer_anciens(cls):
        """
        Supprime définitivement les utilisateurs dont le délai est expiré.

        Cette méthode doit être appelée périodiquement pour finaliser
        la suppression des utilisateurs dont le délai de 5 minutes
        de restauration est écoulé.

        Processus:
            1. Identifier les utilisateurs supprimés depuis plus de 5 min
            2. Pour chaque utilisateur:
                a. Créer une entrée dans HistoriqueSuppressionUtilisateur
                b. Supprimer les fichiers EDI (CSV) associés aux commandes
            3. Supprimer les enregistrements UtilisateurSupprime

        Note:
            Les fichiers EDI sont stockés dans le répertoire
            C:\\Users\\Giffaud\\Documents\\Site_extranet\\edi_exports

        Example:
            >>> # Appelé périodiquement par une tâche planifiée
            >>> UtilisateurSupprime.nettoyer_anciens()
        """
        import os
        from pathlib import Path

        # Chemin vers le répertoire des exports EDI
        EDI_OUTPUT_DIR = Path(r'C:\Users\Giffaud\Documents\Site_extranet\edi_exports')

        # Calculer la date limite (5 minutes dans le passé)
        limite = timezone.now() - timedelta(minutes=5)

        # Récupérer tous les utilisateurs supprimés depuis plus de 5 minutes
        anciens = cls.objects.filter(date_suppression__lt=limite)

        for utilisateur in anciens:
            # Créer l'entrée dans l'historique pour traçabilité
            nb_commandes = len(utilisateur.commandes_json)
            HistoriqueSuppressionUtilisateur.objects.create(
                username=utilisateur.username,
                nom_client=utilisateur.nom_client,
                code_tiers=utilisateur.code_tiers,
                nb_commandes=nb_commandes,
            )

            # Supprimer les fichiers CSV EDI associés aux commandes
            # Ces fichiers contiennent les données de commande au format EDI
            for commande in utilisateur.commandes_json:
                numero = commande.get('numero', '')
                if numero:
                    fichier_edi = EDI_OUTPUT_DIR / f"{numero}.csv"
                    if fichier_edi.exists():
                        try:
                            os.remove(fichier_edi)
                        except OSError:
                            # En cas d'erreur (fichier verrouillé, etc.), continuer
                            pass

        # Supprimer tous les enregistrements UtilisateurSupprime traités
        anciens.delete()
