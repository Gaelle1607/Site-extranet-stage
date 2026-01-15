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
        },
        {
            'reference': 'PORC002',
            'nom': 'Côtes de porc',
            'description': 'Côtes de porc fermier',
            'categorie': 'Porc',
            'prix': 8.90,
            'unite': 'kg',
            'stock': 30,
        },
        {
            'reference': 'PORC003',
            'nom': 'Saucisses',
            'description': 'Saucisses de porc fermier',
            'categorie': 'Charcuterie',
            'prix': 9.50,
            'unite': 'kg',
            'stock': 25,
        },
        {
            'reference': 'BOEUF001',
            'nom': 'Entrecôte',
            'description': 'Entrecôte de bœuf',
            'categorie': 'Bœuf',
            'prix': 24.90,
            'unite': 'kg',
            'stock': 20,
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
