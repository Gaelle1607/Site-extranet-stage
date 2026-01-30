from django.db import models
from django.contrib.auth.models import User


class Utilisateur(models.Model):
    """Compte utilisateur pour l'authentification sur le site"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='utilisateur')
    # Code tiers pour lier à la table comcli distante
    code_tiers = models.CharField('Code tiers', max_length=50)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.user.username} - {self.code_tiers}"

    def get_client_distant(self):
        """Récupère les infos client depuis la base distante (priorité aux entrées avec complement vide)"""
        from django.db import connections
        from types import SimpleNamespace

        with connections['logigvd'].cursor() as cursor:
            # D'abord chercher une entrée avec complement vide (ORDER BY nom pour cohérence)
            cursor.execute("""
                SELECT nom, complement, adresse, cp, acheminement FROM comcli
                WHERE tiers = %s AND (complement IS NULL OR TRIM(complement) = '')
                ORDER BY nom
                LIMIT 1
            """, [self.code_tiers])
            row = cursor.fetchone()
            if not row:
                # Sinon prendre la première entrée triée par complement
                cursor.execute("""
                    SELECT nom, complement, adresse, cp, acheminement FROM comcli
                    WHERE tiers = %s ORDER BY complement, nom LIMIT 1
                """, [self.code_tiers])
                row = cursor.fetchone()

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
    """Demande de réinitialisation de mot de passe"""
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='demandes_mdp',
        verbose_name='Utilisateur'
    )
    date_demande = models.DateTimeField('Date de demande', auto_now_add=True)
    traitee = models.BooleanField('Traitée', default=False)
    date_traitement = models.DateTimeField('Date de traitement', null=True, blank=True)

    class Meta:
        verbose_name = 'Demande de mot de passe'
        verbose_name_plural = 'Demandes de mot de passe'
        ordering = ['-date_demande']

    def __str__(self):
        return f"Demande de {self.utilisateur.user.username} - {self.date_demande.strftime('%d/%m/%Y %H:%M')}"
