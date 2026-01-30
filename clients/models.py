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
        """Récupère les infos client depuis la base distante"""
        from catalogue.models import ComCli
        return ComCli.objects.using('logigvd').filter(tiers=self.code_tiers).first()


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
