from django.db import models
from django.contrib.auth.models import User


class Utilisateur(models.Model):
    """Compte utilisateur pour l'authentification sur le site"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='utilisateur')
    # Code tiers pour lier à la table comcli distante
    code_tiers = models.CharField('Code tiers', max_length=50)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.user.username} - {self.code_tiers}"

    def get_client_distant(self):
        """Récupère les infos client depuis la base distante"""
        from catalogue.models import ComCli
        try:
            return ComCli.objects.using('logigvd').get(tiers=self.code_tiers)
        except ComCli.DoesNotExist:
            return None
