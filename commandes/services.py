"""
Service d'envoi des commandes au logiciel externe.

À adapter selon votre logiciel de gestion :
- API REST
- SOAP/XML
- Base de données
- Email
- Fichier CSV/Excel
- etc.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def envoyer_commande(commande_data):
    """
    Envoie une commande au logiciel externe.

    Args:
        commande_data: Dictionnaire contenant :
            - client: Nom du client
            - lignes: Liste des lignes de commande
                - reference: Référence produit
                - nom: Nom du produit
                - quantite: Quantité commandée
                - prix: Prix unitaire
                - total: Total ligne
            - total: Total de la commande
            - notes: Notes/commentaires

    Returns:
        dict: Résultat de l'envoi (référence, statut, etc.)

    Raises:
        Exception: En cas d'erreur d'envoi
    """
    # TODO: Implémenter selon votre logiciel

    # Exemple API REST:
    # import requests
    # response = requests.post(
    #     'https://api.votrelogiciel.com/commandes',
    #     json=commande_data,
    #     headers={'Authorization': 'Bearer VOTRE_TOKEN'}
    # )
    # response.raise_for_status()
    # return response.json()

    # Exemple envoi par email:
    # from django.core.mail import send_mail
    # send_mail(
    #     subject=f"Nouvelle commande - {commande_data['client']}",
    #     message=formater_commande(commande_data),
    #     from_email='extranet@giffaudgroupe.fr',
    #     recipient_list=['commandes@giffaudgroupe.fr'],
    # )

    # Pour le moment : log de la commande
    logger.info(f"=== NOUVELLE COMMANDE ===")
    logger.info(f"Client: {commande_data['client']}")
    logger.info(f"Date: {datetime.now()}")
    logger.info(f"Articles:")
    for ligne in commande_data['lignes']:
        logger.info(f"  - {ligne['reference']} : {ligne['nom']} x{ligne['quantite']} = {ligne['total']}€")
    logger.info(f"Total: {commande_data['total']}€")
    if commande_data.get('notes'):
        logger.info(f"Notes: {commande_data['notes']}")
    logger.info(f"=========================")

    # Simuler un succès
    return {
        'success': True,
        'message': 'Commande envoyée (mode test)',
    }
