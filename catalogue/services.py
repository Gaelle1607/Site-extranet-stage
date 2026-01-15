"""
Service pour récupérer les produits et prix depuis une source externe.

À adapter selon votre logiciel de gestion :
- API REST
- Base de données externe
- Fichier CSV/Excel
- etc.
"""


def get_produits_client(client):
    """
    Récupère la liste des produits avec prix pour un client.

    Args:
        client: Instance Client

    Returns:
        Liste de dictionnaires avec les produits :
        [
            {
                'reference': 'REF001',
                'nom': 'Produit 1',
                'description': 'Description...',
                'categorie': 'Catégorie A',
                'prix': 10.50,
                'unite': 'kg',
                'stock': 100,  # optionnel
                'image': 'url_image',  # optionnel
                'nb_commandes': 5,  # optionnel - nombre de fois commandé par ce client
            },
            ...
        ]
    """
    # TODO: Implémenter la récupération depuis votre source externe
    # Exemple avec API REST:
    # import requests
    # response = requests.get(f'https://api.votrelogiciel.com/produits/{client.nom}')
    # return response.json()

    # Données de test
    return [
        {
            'reference': 'PORC001',
            'nom': 'Filet mignon de porc',
            'description': 'Filet mignon de porc fermier',
            'categorie': 'Porc',
            'prix': 12.50,
            'unite': 'kg',
            'stock': 50,
            'nb_commandes': 3,
        },
        {
            'reference': 'PORC002',
            'nom': 'Côtes de porc',
            'description': 'Côtes de porc fermier',
            'categorie': 'Porc',
            'prix': 8.90,
            'unite': 'kg',
            'stock': 30,
            'nb_commandes': 12,  # Favori
        },
        {
            'reference': 'PORC003',
            'nom': 'Saucisses',
            'description': 'Saucisses de porc fermier',
            'categorie': 'Charcuterie',
            'prix': 9.50,
            'unite': 'kg',
            'stock': 25,
            'nb_commandes': 8,  # Favori
        },
        {
            'reference': 'BOEUF001',
            'nom': 'Entrecôte',
            'description': 'Entrecôte de bœuf',
            'categorie': 'Bœuf',
            'prix': 24.90,
            'unite': 'kg',
            'stock': 20,
            'nb_commandes': 2,
        },
        {
            'reference': 'BOEUF002',
            'nom': 'Faux-filet',
            'description': 'Faux-filet de bœuf persillé',
            'categorie': 'Bœuf',
            'prix': 22.50,
            'unite': 'kg',
            'stock': 15,
            'nb_commandes': 0,
        },
        {
            'reference': 'BOEUF003',
            'nom': 'Bavette',
            'description': 'Bavette de bœuf tendre',
            'categorie': 'Bœuf',
            'prix': 18.90,
            'unite': 'kg',
            'stock': 25,
            'nb_commandes': 1,
        },
        {
            'reference': 'VOLAILLE001',
            'nom': 'Poulet fermier',
            'description': 'Poulet fermier entier Label Rouge',
            'categorie': 'Volaille',
            'prix': 9.80,
            'unite': 'kg',
            'stock': 40,
            'nb_commandes': 15,  # Favori
        },
        {
            'reference': 'VOLAILLE003',
            'nom': 'Cuisses de poulet',
            'description': 'Cuisses de poulet fermier - Barquette de 4 pièces (environ 1,2 kg)',
            'categorie': 'Volaille',
            'prix': 7.90,
            'unite': 'barquette',
            'stock': 50,
            'image': '/static/images/produits/cuisses-poulet.jpg',
            'nb_commandes': 20,  # Favori - le plus commandé
        },
        {
            'reference': 'VOLAILLE002',
            'nom': 'Cuisses de canard',
            'description': 'Cuisses de canard confites',
            'categorie': 'Volaille',
            'prix': 14.50,
            'unite': 'kg',
            'stock': 20,
            'nb_commandes': 0,
        },
        {
            'reference': 'CHARC001',
            'nom': 'Jambon blanc',
            'description': 'Jambon blanc supérieur sans nitrite',
            'categorie': 'Charcuterie',
            'prix': 16.90,
            'unite': 'kg',
            'stock': 35,
            'nb_commandes': 5,
        },
        {
            'reference': 'CHARC002',
            'nom': 'Pâté de campagne',
            'description': 'Pâté de campagne artisanal',
            'categorie': 'Charcuterie',
            'prix': 11.50,
            'unite': 'kg',
            'stock': 30,
            'nb_commandes': 0,
        },
    ]


def get_categories_client(client):
    """
    Récupère les catégories disponibles pour un client.

    Returns:
        Liste de noms de catégories
    """
    # TODO: Implémenter selon votre source
    produits = get_produits_client(client)
    categories = list(set(p.get('categorie', '') for p in produits if p.get('categorie')))
    return sorted(categories)


def get_produit_by_reference(client, reference):
    """
    Récupère un produit par sa référence.

    Returns:
        Dictionnaire du produit ou None
    """
    # TODO: Optimiser avec un appel direct à l'API
    produits = get_produits_client(client)
    for p in produits:
        if p['reference'] == reference:
            return p
    return None
