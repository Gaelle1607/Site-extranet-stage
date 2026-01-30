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
import os
from datetime import datetime
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

# Configuration EDI
EDI_CONFIG = {
    'SENDER_GLN': '3020476104320',           # GLN expéditeur (à configurer)
    'RECEIVER_GLN': '3014853100104',         # GLN destinataire (à configurer)
    'SUPPLIER_GLN': '3014853100104',         # GLN fournisseur
    'SUPPLIER_NAME': 'LES DELICES DE CLOBERT',
    'SUPPLIER_ADDRESS': 'ZI DE MONTFORT',
    'SUPPLIER_CP': '85590',
    'SUPPLIER_CITY': 'LES EPESSES',
    'SUPPLIER_COUNTRY': 'FR',
}

# Dossier de sortie des fichiers CSV
EDI_OUTPUT_DIR = Path(r'C:\Users\Giffaud\Documents\Site_extranet\edi_exports')


def generer_csv_edi(commande, client, lignes):
    """
    Génère un fichier CSV au format EDI ORDERS pour une commande.

    Args:
        commande: Instance Commande
        client: Instance ComCli (infos client)
        lignes: Liste des lignes de commande avec infos produits

    Returns:
        str: Chemin du fichier CSV généré
    """
    print(f"EDI: === Début génération EDI pour commande {commande.numero} ===")
    print(f"EDI: Dossier cible: {EDI_OUTPUT_DIR}")
    logger.info(f"=== Début génération EDI pour commande {commande.numero} ===")
    logger.info(f"Dossier cible: {EDI_OUTPUT_DIR}")

    # Créer le dossier si nécessaire
    os.makedirs(EDI_OUTPUT_DIR, exist_ok=True)
    print(f"EDI: Dossier existe: {EDI_OUTPUT_DIR.exists()}")
    logger.info(f"Dossier créé/vérifié: {EDI_OUTPUT_DIR.exists()}")

    # Nom du fichier
    filename = f"{commande.numero}.csv"
    filepath = EDI_OUTPUT_DIR / filename

    # Préparer les données
    date_commande = commande.date_commande.strftime('%d/%m/%Y')
    heure_commande = commande.date_commande.strftime('%H:%M')

    # Gérer les dates qui peuvent être des strings ou des objets date
    if commande.date_livraison:
        if hasattr(commande.date_livraison, 'strftime'):
            date_livraison = commande.date_livraison.strftime('%d/%m/%Y')
        else:
            from datetime import datetime as dt
            date_livraison = dt.strptime(str(commande.date_livraison), '%Y-%m-%d').strftime('%d/%m/%Y')
    else:
        date_livraison = ''

    if commande.date_depart_camions:
        if hasattr(commande.date_depart_camions, 'strftime'):
            date_depart = commande.date_depart_camions.strftime('%d/%m/%Y')
        else:
            from datetime import datetime as dt
            date_depart = dt.strptime(str(commande.date_depart_camions), '%Y-%m-%d').strftime('%d/%m/%Y')
    else:
        date_depart = ''

    # GLN client (utiliser le code tiers comme base si pas de GLN)
    client_gln = f"302{str(client.tiers).zfill(10)}" if client else ''
    client_code = str(client.tiers) if client else ''
    client_nom = client.nom if client else ''
    client_adresse = client.adresse or '' if client else ''
    client_cp = client.cp or '' if client else ''
    client_ville = client.acheminement or '' if client else ''

    # Nombre de lignes
    nb_lignes = len(lignes)

    # Construire le contenu CSV (format EDI ORDERS)
    csv_lines = []

    # Ligne @GP: Header
    csv_lines.append(f"@GP,WEB@EDI,ORDERS,STANDARD,{EDI_CONFIG['SENDER_GLN']},,{EDI_CONFIG['RECEIVER_GLN']},,{commande.numero},,,,,,,,,,,")
    csv_lines.append(",,,,,,,,,,,,,,,,,,,")

    # Ligne ENT: Entête commande
    csv_lines.append(f"ENT,220,{commande.numero},{date_commande},{heure_commande},EUR,{date_livraison},00:00,,,0,,{nb_lignes},,,,,,,")
    csv_lines.append(",,,,,,,,,,,,,,,,,,,")

    # Ligne DTM: Date livraison
    csv_lines.append(f"DTM,2,{date_livraison},00:00,,,,,,,,,,,,,,,,")
    csv_lines.append(",,,,,,,,,,,,,,,,,,,")

    # Ligne PAR BY: Acheteur (client)
    csv_lines.append(f"PAR,BY,{client_gln},{client_code},{client_nom},{client_adresse},,,{client_cp},{client_ville},FR,,,,,,,,,")
    csv_lines.append(",,,,,,,,,,,,,,,,,,,")

    # Ligne PAR SU: Fournisseur
    csv_lines.append(f"PAR,SU,{EDI_CONFIG['SUPPLIER_GLN']},,{EDI_CONFIG['SUPPLIER_NAME']},{EDI_CONFIG['SUPPLIER_ADDRESS']},,,{EDI_CONFIG['SUPPLIER_CP']},{EDI_CONFIG['SUPPLIER_CITY']},{EDI_CONFIG['SUPPLIER_COUNTRY']},,,,,,,,,")
    csv_lines.append(",,,,,,,,,,,,,,,,,,,")

    # Ligne PAR DP: Point de livraison (même que l'acheteur)
    csv_lines.append(f"PAR,DP,{client_gln},{client_code},{client_nom},{client_adresse},,,{client_cp},{client_ville},FR,,,,,,,,,")
    csv_lines.append(",,,,,,,,,,,,,,,,,,,")

    # Lignes LIG: Produits
    for i, ligne in enumerate(lignes, 1):
        reference = ligne.get('reference', '')
        nom = ligne.get('nom', '')
        quantite = ligne.get('quantite', 0)
        prix = float(ligne.get('prix', 0))
        total = float(ligne.get('total', prix * quantite))

        csv_lines.append(f"LIG,{i},{reference},,,{quantite},{float(quantite):.3f},PCE,{prix:.6f},{nom},,,,,,,,,,{total:.6f}")
        csv_lines.append(",,,,,,,,,,,,,,,,,,,")

    # Ligne END: Fin
    csv_lines.append("END,,,,,,,,,,,,,,,,,,,")
    csv_lines.append(",,,,,,,,,,,,,,,,,,,")

    # Ligne @ND: Fin document
    csv_lines.append("@ND,,,,,,,,,,,,,,,,,,,")

    # Écrire le fichier
    logger.info(f"Écriture du fichier: {filepath}")
    print(f"EDI: Écriture du fichier: {filepath}")

    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(csv_lines))

    logger.info(f"Fichier EDI généré avec succès: {filepath}")
    print(f"EDI: Fichier généré avec succès: {filepath}")

    return str(filepath)


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
