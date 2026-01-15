from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    """Profil client B2B - minimal"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client')
    nom = models.CharField('Nom / Société', max_length=200)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['nom']

    def __str__(self):
        return self.nom
