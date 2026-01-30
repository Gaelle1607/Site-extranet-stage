"""
Service pour récupérer les produits et prix depuis la base MariaDB distante.
"""
import unicodedata
import re
from collections import Counter

from django.db import connections

from .models import ComCli, ComCliLig, Catalogue, Prod


def _normaliser(texte):
    """Retire les accents et met en minuscule pour la comparaison."""
    return unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('ascii').lower()


# Mots à ignorer pour les filtres automatiques
MOTS_IGNORES = {
    # Articles et prépositions
    'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'au', 'aux', 'en', 'et', 'ou', 'a', 'par',
    'pour', 'avec', 'sans', 'sur', 'sous', 'dans', 'entre',
    # Unités et mesures
    'kg', 'gr', 'g', 'ml', 'cl', 'l', 'pce', 'pcs', 'env', 'environ', 'mini', 'maxi', 'max', 'min',
    # Nombres
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12', '15', '20', '25', '30', '50', '100',
    # Mots trop génériques
    'viande', 'piece', 'pieces', 'tranche', 'tranches', 'lot', 'x', 'n', 'type', 'vide', 'col',
    'demi', 'sup', 'sel', 'sat', 'mensec', 'noir', 'sauc',
}


def _get_termes_manuels():
    """Récupère tous les termes déjà couverts par les filtres manuels."""
    termes = set()
    for groupe in FILTRES_DISPONIBLES.values():
        for info in groupe.values():
            termes.update(info.get("termes", []))
    return termes


def generer_filtres_automatiques(produits, seuil_occurrences=3):
    """
    Génère des filtres automatiques à partir des libellés des produits.
    Exclut les termes déjà couverts par les filtres manuels (approche hybride).

    Args:
        produits: Liste des produits avec leurs libellés
        seuil_occurrences: Nombre minimum d'occurrences pour créer un filtre

    Returns:
        Dictionnaire {code: {"label": label, "termes": [termes]}}
    """
    # Récupérer les termes déjà couverts par les filtres manuels
    termes_manuels = _get_termes_manuels()

    # Compter tous les mots significatifs
    compteur_mots = Counter()

    for produit in produits:
        libelle = produit.get('libelle', '') or ''
        # Normaliser et extraire les mots
        libelle_normalise = _normaliser(libelle)
        # Garder uniquement les mots de 3+ caractères
        mots = re.findall(r'\b[a-z]{3,}\b', libelle_normalise)

        # Ne compter chaque mot qu'une fois par produit
        mots_uniques = set(mots)
        for mot in mots_uniques:
            # Exclure les mots ignorés ET les termes déjà dans les filtres manuels
            if mot not in MOTS_IGNORES and mot not in termes_manuels:
                compteur_mots[mot] += 1

    # Créer les filtres pour les mots fréquents
    filtres_auto = {}
    for mot, count in compteur_mots.items():
        if count >= seuil_occurrences:
            # Créer un label avec majuscule
            label = mot.capitalize()
            filtres_auto[f"auto_{mot}"] = {
                "label": f"{label} ({count})",
                "termes": [mot],
                "count": count
            }

    # Trier par nombre d'occurrences décroissant
    filtres_auto = dict(sorted(
        filtres_auto.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    ))

    return filtres_auto


# Filtres organisés par groupe
# Chaque filtre : code -> {"label": affiché, "termes": [cherchés dans le libellé sans accents]}
FILTRES_DISPONIBLES = {
    "Format": {
        "colis":        {"label": "Colis",          "termes": []},  # basé sur l'unité de vente
        "kg":           {"label": "Vente au kg",    "termes": []},  # basé sur l'unité de vente
        "barquette":    {"label": "Barquette",      "termes": ["barquette", "barquettes"]},
        "seau":         {"label": "Seau",           "termes": ["seau", "seaux"]},
        "s/v":          {"label": "S/Vide",         "termes": ["s/vide", "sous vide", "sous-vide"]},
        "s/at":         {"label": "Sous atmosphère","termes": ["s/at", "sous atmosphere"]},
        "quart":        {"label": "Quart",          "termes": ["quart", "quarts"]},
    },
    "Types de viandes": {
        "porc":         {"label": "Porc",           "termes": ["porc", "porcs"]},
        "bovin":        {"label": "Bovin",          "termes": ["boeuf", "boeufs", "veau", "veaux", "bovin", "bovins"]},
        "poulet":       {"label": "Poulet",         "termes": ["poulet", "poulets"]},
        "canard":       {"label": "Canard",         "termes": ["canard", "canards"]},
        "lapin":        {"label": "Lapin",          "termes": ["lapin", "lapins"]},
        "saumon":       {"label": "Saumon",         "termes": ["saumon", "saumons"]},
    },
    "Découpes / morceaux": {
        "echine":       {"label": "Échine",         "termes": ["echine", "echines"]},
        "filet":        {"label": "Filet",          "termes": ["filet", "filets"]},
        "cote":         {"label": "Côte",           "termes": ["cote", "cotes"]},
        "poitrine":     {"label": "Poitrine",       "termes": ["poitrine", "poitrines"]},
        "jambon":       {"label": "Jambon",         "termes": ["jambon", "jambons"]},
        "palette":      {"label": "Palette",        "termes": ["palette", "palettes"]},
        "epaule":       {"label": "Épaule",         "termes": ["epaule", "epaules"]},
        "jarret":       {"label": "Jarret",         "termes": ["jarret", "jarrets"]},
        "cuisse":       {"label": "Cuisse",         "termes": ["cuisse", "cuisses"]},
        "rouelle":      {"label": "Rouelle",        "termes": ["rouelle", "rouelles"]},
        "onglet":       {"label": "Onglet",         "termes": ["onglet", "onglets"]},
        "araignee":     {"label": "Araignée",       "termes": ["araignee", "araignees"]},
        "maigre":       {"label": "Maigre",         "termes": ["maigre", "maigres"]},
        "gras":         {"label": "Gras",           "termes": ["gras"]},
        "noix":         {"label": "Noix",           "termes": ["noix"]},
        "queue":        {"label": "Queue",          "termes": ["queue", "queues"]},
        "tete":         {"label": "Tête",           "termes": ["tete", "tetes"]},
        "mignon":       {"label": "Mignon",         "termes": ["mignon", "mignons"]},
    },
    "Spécifiques porc": {
        "travers":      {"label": "Travers",        "termes": ["travers"]},
        "ribs":         {"label": "Ribs",           "termes": ["ribs"]},
        "paletot":      {"label": "Paletot",        "termes": ["paletot", "paletots"]},
    },
    "Charcuterie": {
        "saucisse":     {"label": "Saucisse",       "termes": ["saucisse", "saucisses"]},
        "chipolata":    {"label": "Chipolata",      "termes": ["chipolata", "chipolatas", "chipo", "chipos"]},
        "merguez":      {"label": "Merguez",        "termes": ["merguez"]},
        "boudin":       {"label": "Boudin",         "termes": ["boudin", "boudins"]},
        "andouillette": {"label": "Andouillette",   "termes": ["andouillette", "andouillettes"]},
        "saucisson":    {"label": "Saucisson",      "termes": ["saucisson", "saucissons"]},
        "rillettes":    {"label": "Rillettes",      "termes": ["rillettes"]},
        "rillauds":     {"label": "Rillauds",       "termes": ["rillauds"]},
        "pate":         {"label": "Pâté",           "termes": ["pate", "pates"]},
        "terrine":      {"label": "Terrines",       "termes": ["terrine", "terrines"]},
        "tortillade":   {"label": "Tortillades",    "termes": ["tortillade", "tortillades"]},
        "tripes":       {"label": "Tripes / Boyaux","termes": ["tripes", "boyaux", "rognon", "rognons", "rein", "reins"]},
        "langouille":   {"label": "Langouille",     "termes": ["langouille", "langouilles"]},
    },
    "Prêts à cuire": {
        "paupiette":    {"label": "Paupiette",      "termes": ["paupiette", "paupiettes"]},
        "brochette":    {"label": "Brochette",      "termes": ["brochette", "brochettes", "broch"]},
        "grillade":     {"label": "Grillade",       "termes": ["grillade", "grillades"]},
        "barbecue":     {"label": "Barbecue",       "termes": ["barbecue", "barbecues", "bbq"]},
        "wok":          {"label": "Wok",            "termes": ["wok", "woks"]},
        "saute":        {"label": "Sauté",          "termes": ["saute", "sautes"]},
        "tomates_farcies": {"label": "Tomates farcies", "termes": ["tomates farcies", "tomate farcie"]},
        "paysanne":     {"label": "Paysanne",       "termes": ["paysanne", "paysannes"]},
        "surprise_paprika": {"label": "Surprise paprika", "termes": ["surprise paprika"]},
        "tartinable":   {"label": "Tartinable",     "termes": ["tartinable", "tartinables"]},
        "roti":         {"label": "Rôti",           "termes": ["roti", "rotis"]},
        "precuit":      {"label": "Précuit",        "termes": ["precuit", "precuits", "pre-cuit"]},
        "orloff":       {"label": "Orloff",         "termes": ["orloff"]},
    },
    "Conservation": {
        "frais":        {"label": "Frais",          "termes": ["frais"]},
        "surgele":      {"label": "Surgelé",        "termes": ["surgele", "surgeles", "congele", "congeles"]},
    },

    "Fromages": {
        "comte":        {"label": "Comté",          "termes": ["comte", "comtes"]},
        "emmental":     {"label": "Emmental",       "termes": ["emmental", "emmentals"]},
        "chevre":       {"label": "Chèvre",         "termes": ["chevre", "chevres"]},
        "reblochon":    {"label": "Reblochon",      "termes": ["reblochon", "reblochons"]},
        "camenbert":    {"label": "Camembert",      "termes": ["camenbert", "camenberts", "camembert", "camemberts"]},
        "bleu":         {"label": "Bleu",           "termes": ["bleu d'auvergne", "bleu de bresse", "bleu de gex", "fourme", "fourmes"]},
    },

    "Qualité": {
        "fermiere":     {"label": "Viande fermière","termes": ["fermiere", "fermieres", "fermier", "fermiers"]},
        "bbc":          {"label": "Bleu Blanc Coeur","termes": ["bleu blanc coeur", "bbc"]},
        "label_rouge":  {"label": "Label Rouge",    "termes": ["label rouge"]},
        "vpf" :  {"label": "Viande de Porc Française",    "termes": ["vpf"]},
    },
    "Origine": {
        "vendeenne":    {"label": "Vendéenne",      "termes": ["vendeenne", "vendeennes", "vendeen", "vendeens", "vendee"]},
        "toulouse":     {"label": "Toulouse",       "termes": ["toulouse"]},
    },

    "Saveurs / Arômes": {
        "nature":       {"label": "Nature",         "termes": ["nature", "natures"]},
        "trad":         {"label": "Traditionnelle", "termes": ["trad", "traditionnelle", "traditionnelles", "traditionnel", "traditionnels"]},
        "piment":       {"label": "Pimenté",        "termes": ["piment", "piments", "pimente", "pimentes"]},
        "espelette":    {"label": "Espelette",      "termes": ["espelette"]},
        "citron":       {"label": "Citron",         "termes": ["citron", "citrons"]},
        "thym":         {"label": "Thym",           "termes": ["thym", "thyms"]},
        "fume":         {"label": "Fumé",           "termes": ["fume", "fumes", "fumee", "fumees"]},
        "herbes":       {"label": "Aux herbes",     "termes": ["herbe", "herbes"]},
        "echalote":     {"label": "Échalote",       "termes": ["echalote", "echalotes"]},
        
    },

    "Autres": {
        "foie_gras":    {"label": "Foie gras",      "termes": ["foie gras"]},
        "magret":       {"label": "Magret",         "termes": ["magret", "magrets"]},
        "miel":         {"label": "Miel",           "termes": ["miel", "miels"]}
    },
}


def get_client_distant(code_tiers):
    """
    Récupère les informations client depuis la base distante.

    Args:
        code_tiers: Code tiers du client

    Returns:
        Instance ComCli ou None
    """
    return ComCli.objects.using('logigvd').filter(tiers=code_tiers).first()


def get_produits_client(utilisateur):
    """
    Récupère la liste des produits avec prix pour un utilisateur.
    Utilise une seule requête SQL avec JOINs pour optimiser les performances.

    Args:
        utilisateur: Instance Utilisateur (avec code_tiers)

    Returns:
        Liste de dictionnaires avec les produits
    """
    code_tiers = utilisateur.code_tiers if hasattr(utilisateur, 'code_tiers') else None

    if not code_tiers:
        return []

    with connections['logigvd'].cursor() as cursor:
        # Requête 1 : catalogue + libellé produit (rapide, catalogue filtré par tiers)
        cursor.execute("""
            SELECT c.prod, p.libelle
            FROM catalogue c
            LEFT JOIN prod p ON c.prod = p.prod
            WHERE c.tiers = %s
        """, [code_tiers])
        catalogue_rows = cursor.fetchall()

        if not catalogue_rows:
            return []

        codes_produits = [r[0] for r in catalogue_rows]
        libelles = {r[0]: r[1] for r in catalogue_rows}

        # Requête 2 : prix et quantités depuis comclilig, filtré par client via comcli
        placeholders = ','.join(['%s'] * len(codes_produits))
        cursor.execute(f"""
            SELECT l.prod, MAX(l.pu_base), MAX(l.qte), MAX(l.poids), MAX(l.colis)
            FROM comclilig l
            INNER JOIN comcli c ON l.comcli = c.comcli AND l.lieusais = c.lieusais
            WHERE c.tiers = %s AND l.prod IN ({placeholders})
            GROUP BY l.prod
        """, [code_tiers] + codes_produits)
        lignes = {r[0]: r[1:] for r in cursor.fetchall()}

    produits = []
    for prod_code in codes_produits:
        ligne = lignes.get(prod_code)
        libelle = libelles.get(prod_code) or prod_code
        pu_base = float(ligne[0]) if ligne and ligne[0] else 0
        poids = float(ligne[2]) if ligne and ligne[2] else 0
        colis = int(ligne[3]) if ligne and ligne[3] else 0

        # Déterminer l'unité de vente
        if poids > 0:
            unite = 'kg'
        elif colis > 0:
            unite = 'Colis'
        else:
            unite = ''

        if pu_base <= 0:
            continue

        # Générer les tags à partir du libellé pour le filtrage
        nom_normalise = _normaliser(libelle) if libelle else ''
        tags = [
            code
            for groupe in FILTRES_DISPONIBLES.values()
            for code, info in groupe.items()
            if any(terme in nom_normalise for terme in info["termes"])
        ]

        # Tags basés sur l'unité de vente
        if unite == 'kg':
            tags.append('kg')
        elif unite == 'Colis':
            tags.append('colis')

        produit = {
            'prod': prod_code,
            'reference': prod_code,
            'libelle': libelle,
            'nom': libelle,
            'pu_base': pu_base,
            'prix': pu_base,
            'unite': unite,
            'nb_commandes': int(ligne[1]) if ligne and ligne[1] else 0,
            'poids': poids,
            'colis': colis,
            'tags': tags,
        }
        produits.append(produit)

    return produits


def get_categories_client(utilisateur):
    """
    Récupère les catégories disponibles pour un utilisateur.

    Returns:
        Liste de noms de catégories
    """
    produits = get_produits_client(utilisateur)
    categories = set()
    for p in produits:
        for cat in p.get('categories', []):
            categories.add(cat)
    return sorted(categories)


def get_produit_by_reference(utilisateur, reference):
    """
    Récupère un produit par sa référence.

    Returns:
        Dictionnaire du produit ou None
    """
    produits = get_produits_client(utilisateur)
    for p in produits:
        if p['reference'] == reference:
            return p
    return None
