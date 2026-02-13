"""
=============================================================================
MODELS.PY - Modèles de l'application Administration
=============================================================================

Cette application ne définit pas de modèles propres car elle utilise
les modèles des autres applications :
    - clients.Utilisateur : Gestion des utilisateurs
    - commandes.Commande : Gestion des commandes
    - catalogue.* : Accès au catalogue produits

L'application administration est principalement composée de vues qui
agrègent et présentent les données des autres applications.

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.db import models

# Aucun modèle spécifique à cette application
# Les modèles utilisés proviennent des applications clients et commandes
