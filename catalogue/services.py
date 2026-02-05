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
    'demi', 'sup', 'sel', 'sat', 'mensec', 'noir', 'sauc', 'unite', 'vrac', 'colis', 'l', 'lunite','dlc','courte','fine',
    'psh','skin','petit','pret','cuire',
    # Mots trop courts ou génériques
    'court', 'eco', 'cuisine', 'tranch', 'cais', 'grand', 'mere',
    # Mots associés à bière (brune/blonde)
    'brune', 'brunes', 'blonde', 'blondes',
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
    # ===== CONDITIONNEMENT =====
    "Format / Conditionnement": {
        "kg":           {"label": "Vente au kg",    "termes": []},  # basé sur unite_fact = 2
        "unite":        {"label": "À l'unité",      "termes": []},  # basé sur unite_fact = 1
        "barquette":    {"label": "Barquette",      "termes": ["barquette", "barquettes", "barq", "barqu"]},
        "carton":       {"label": "Carton",         "termes": ["carton", "cartons", "cart"]},
        "seau":         {"label": "Seau",           "termes": ["seau", "seaux"]},
        "plateau":      {"label": "Plateau",        "termes": ["plateau"]},
        "vrac":         {"label": "Vrac",           "termes": ["vrac"]},
        "s/v":          {"label": "Sous vide",      "termes": ["s/vide", "sous vide", "sous-vide"]},
        "s/at":         {"label": "Sous atmosphère","termes": ["s/at", "sous atmosphere"]},
        "opercule":     {"label": "Operculé",       "termes": ["opercule", "opercules", "operculee", "operculees"]},
        "entier":       {"label": "Entier",         "termes": ["entier", "entiers", "entiere", "entieres"]},
        "quart":        {"label": "Quart",          "termes": ["quart", "quarts"]},
        "tranchee":     {"label": "Tranchée",       "termes": ["tranchee", "tranchees"]},
        "ficelle":      {"label": "Ficelle",        "termes": ["ficelle", "ficelles"]},
    },

    # ===== VIANDES =====
    "Types de viandes": {
        "porc":         {"label": "Porc",           "termes": ["porc", "porcs"]},
        "bovin":        {"label": "Bovin",          "termes": ["boeuf", "boeufs", "veau", "veaux", "bovin", "bovins"]},
        "poulet":       {"label": "Poulet",         "termes": ["poulet", "poulets"]},
        "dinde":        {"label": "Dinde",          "termes": ["dinde", "dindes"]},
        "canard":       {"label": "Canard",         "termes": ["canard", "canards"]},
        "chapon":       {"label": "Chapon",         "termes": ["chapon", "chapons"]},
        "pintade":      {"label": "Pintade",        "termes": ["pintade", "pintades"]},
        "lapin":        {"label": "Lapin",          "termes": ["lapin", "lapins"]},
        "saumon":       {"label": "Saumon",         "termes": ["saumon", "saumons"]},
    },

    "Découpes / Morceaux": {
        "filet":        {"label": "Filet",          "termes": ["filet", "filets"]},
        "cote":         {"label": "Côte",           "termes": ["cote", "cotes"]},
        "echine":       {"label": "Échine",         "termes": ["echine", "echines"]},
        "epaule":       {"label": "Épaule",         "termes": ["epaule", "epaules"]},
        "cuisse":       {"label": "Cuisse",         "termes": ["cuisse", "cuisses"]},
        "poitrine":     {"label": "Poitrine",       "termes": ["poitrine", "poitrines"]},
        "jambon":       {"label": "Jambon",         "termes": ["jambon", "jambons"]},
        "palette":      {"label": "Palette",        "termes": ["palette", "palettes"]},
        "jarret":       {"label": "Jarret",         "termes": ["jarret", "jarrets"]},
        "rouelle":      {"label": "Rouelle",        "termes": ["rouelle", "rouelles"]},
        "mignon":       {"label": "Mignon",         "termes": ["mignon", "mignons"]},
        "onglet":       {"label": "Onglet",         "termes": ["onglet", "onglets"]},
        "araignee":     {"label": "Araignée",       "termes": ["araignee", "araignees"]},
        "noix":         {"label": "Noix",           "termes": ["noix"]},
        "blancs":       {"label": "Blancs",         "termes": ["blancs", "blanc"]},
        "emince":       {"label": "Émincé",         "termes": ["emince", "eminces"]},
        "palet":        {"label": "Palet",          "termes": ["palet", "palets"]},
        "joues":        {"label": "Joues",          "termes": ["joue", "joues"]},
        "foie":         {"label": "Foie",           "termes": ["foie", "foies"]},
        "queue":        {"label": "Queue",          "termes": ["queue", "queues"]},
        "tete":         {"label": "Tête",           "termes": ["tete", "tetes"]},
        "maigre":       {"label": "Maigre",         "termes": ["maigre", "maigres"]},
        "gras":         {"label": "Gras",           "termes": ["gras"]},
        "paree":        {"label": "Parée",          "termes": ["paree", "parees", "pare", "pares"]},
    },

    "Spécifiques porc": {
        "travers":      {"label": "Travers",        "termes": ["travers"]},
        "ribs":         {"label": "Ribs",           "termes": ["ribs"]},
        "paletot":      {"label": "Paletot",        "termes": ["paletot", "paletots"]},
    },

    # ===== CHARCUTERIE =====
    "Charcuterie": {
        "saucisse":     {"label": "Saucisse",       "termes": ["saucisse", "saucisses"]},
        "chipolata":    {"label": "Chipolata",      "termes": ["chipolata", "chipolatas", "chipo", "chipos"]},
        "merguez":      {"label": "Merguez",        "termes": ["merguez"]},
        "boudin":       {"label": "Boudin",         "termes": ["boudin", "boudins"]},
        "andouillette": {"label": "Andouillette",   "termes": ["andouillette", "andouillettes"]},
        "chorizo":      {"label": "Chorizo",        "termes": ["chorizo", "chorizos"]},
        "chorizettes":  {"label": "Chorizettes",    "termes": ["chorizette", "chorizettes"]},
        "crepinettes":  {"label": "Crépinettes",    "termes": ["crepinette", "crepinettes"]},
        "francfort":    {"label": "Francfort",      "termes": ["francfort", "francforts"]},
        "strasbourg":   {"label": "Strasbourg",     "termes": ["strasbourg"]},
        "cervelas":     {"label": "Cervelas",       "termes": ["cervelas"]},
        "saucisson":    {"label": "Saucisson",      "termes": ["saucisson", "saucissons"]},
        "rillettes":    {"label": "Rillettes",      "termes": ["rillettes"]},
        "rillauds":     {"label": "Rillauds",       "termes": ["rillauds"]},
        "pate":         {"label": "Pâté",           "termes": ["pate", "pates"]},
        "terrine":      {"label": "Terrines",       "termes": ["terrine", "terrines"]},
        "tortillade":   {"label": "Tortillades",    "termes": ["tortillade", "tortillades"]},
        "langouille":   {"label": "Langouille",     "termes": ["langouille", "langouilles"]},
        "tripes":       {"label": "Tripes / Boyaux","termes": ["tripes", "boyaux", "rognon", "rognons", "rein", "reins"]},
    },

    # ===== PREPARATIONS =====
    "Préparations": {
        "paupiette":    {"label": "Paupiette",      "termes": ["paupiette", "paupiettes", "paup"]},
        "brochette":    {"label": "Brochette",      "termes": ["brochette", "brochettes", "broch"]},
        "grillade":     {"label": "Grillade",       "termes": ["grillade", "grillades"]},
        "roti":         {"label": "Rôti",           "termes": ["roti", "rotis"]},
        "saute":        {"label": "Sauté",          "termes": ["saute", "sautes"]},
        "farce":        {"label": "Farce / Farci",  "termes": ["farce", "farces", "farci", "farcis", "farcie", "farcies"]},
        "marinade":     {"label": "Marinade",       "termes": ["marinade", "marinades", "marine", "marines"]},
        "confites":     {"label": "Confit",         "termes": ["confite", "confites", "confit", "confits"]},
        "saumure":      {"label": "Saumure",        "termes": ["saumure", "saumures", "saumuree", "saumurees"]},
        "brasse":       {"label": "Brassé / Braisé","termes": ["brasse", "brasses", "braisee", "braisees"]},
        "precuit":      {"label": "Précuit",        "termes": ["precuit", "precuits", "pre-cuit"]},
        "barbecue":     {"label": "Barbecue",       "termes": ["barbecue", "barbecues", "bbq"]},
        "wok":          {"label": "Wok",            "termes": ["wok", "woks"]},
        "tartinable":   {"label": "Tartinable",     "termes": ["tartinable", "tartinables"]},
        "assort":       {"label": "Assortiment",    "termes": ["assort", "assortiment", "assortiments"]},
        "cassolettes":  {"label": "Cassolettes",    "termes": ["cassolette", "cassolettes"]},
        "gourdinade":   {"label": "Gourdinade",     "termes": ["gourdinade", "gourdinades"]},
        "delice":       {"label": "Délice",         "termes": ["delice", "delices"]},
        "tapas":        {"label": "Tapas",          "termes": ["tapas"]},
        "festif":       {"label": "Festif",         "termes": ["festif", "festifs", "festive", "festives"]},
    },

    "Recettes régionales": {
        "vendeenne":    {"label": "Vendéenne",      "termes": ["vendeenne", "vendeennes", "vendeen", "vendeens", "vendee", "ven"]},
        "toulouse":     {"label": "Toulouse",       "termes": ["toulouse"]},
        "provencale":   {"label": "Provençale",     "termes": ["provencale", "provencales", "provencal"]},
        "basquaise":    {"label": "Basquaise",      "termes": ["basquaise", "basquaises"]},
        "savoyard":     {"label": "Savoyard",       "termes": ["savoyard", "savoyards", "savoyarde", "savoyardes"]},
        "montagnard":   {"label": "Montagnard",     "termes": ["montagnard", "montagnards", "montagnarde", "montagnardes"]},
        "tartiflette":  {"label": "Tartiflette",    "termes": ["tartiflette", "tartiflettes"]},
        "choucroute":   {"label": "Choucroute",     "termes": ["choucroute", "choucroutes"]},
        "obernois":     {"label": "Obernois",       "termes": ["obernois", "obernoise", "obernoises"]},
        "potee":        {"label": "Potée",          "termes": ["potee", "potees"]},
        "campagne":     {"label": "Campagne",       "termes": ["campagne", "campagnes"]},
        "paysanne":     {"label": "Paysanne",       "termes": ["paysanne", "paysannes"]},
        "grand_mere":   {"label": "Grand-mère",     "termes": ["grand mere", "grand-mere", "grandmere"]},
        "vigneronne":   {"label": "Vigneronne",     "termes": ["vigneronne", "vigneronnes"]},
        "orloff":       {"label": "Orloff",         "termes": ["orloff"]},
        "brasero":      {"label": "Brasero",        "termes": ["brasero", "braseros"]},
        "maitre_hotel": {"label": "Maître d'hôtel", "termes": ["maitre", "hotel"]},
        "tomates_farcies": {"label": "Tomates farcies", "termes": ["tomates farcies", "tomate farcie"]},
        "surprise_paprika": {"label": "Surprise paprika", "termes": ["surprise paprika"]},
    },

    "Recettes du monde": {
        "mexicaines":   {"label": "Mexicaines",     "termes": ["mexicaine", "mexicaines", "mexicain", "mexicains", "mex", "tex"]},
        "antillais":    {"label": "Antillais",      "termes": ["antillais", "antillaise", "antillaises"]},
        "andalou":      {"label": "Andalou",        "termes": ["andalou", "andalous", "andalouse", "andalouses"]},
        "italienne":    {"label": "Italienne",      "termes": ["italienne", "italiennes", "italien", "italiens"]},
        "indienne":     {"label": "Indienne",       "termes": ["indienne", "indiennes", "indien", "indiens"]},
        "tandoori":     {"label": "Tandoori",       "termes": ["tandoori", "tandooris"]},
        "massala":      {"label": "Massala",        "termes": ["massala", "masala"]},
        "norvegien":    {"label": "Norvégien",      "termes": ["norvegien", "norvegiens", "norvegienne", "norvegiennes"]},
    },

    # ===== CONSERVATION =====
    "Conservation": {
        "frais":        {"label": "Frais",          "termes": ["frais"]},
        "surgele":      {"label": "Surgelé",        "termes": ["surgele", "surgeles", "congele", "congeles"]},
        "crues":        {"label": "Crues",          "termes": ["crues", "crue"]},
        "cuit":         {"label": "Cuit",           "termes": ["cuit", "cuits", "cuite", "cuites"]},
        "sale":         {"label": "Salé",           "termes": ["sale", "sales", "salee", "salees"]},
        "fume":         {"label": "Fumé",           "termes": ["fume", "fumes", "fumee", "fumees"]},
    },

    # ===== QUALITÉ =====
    "Labels / Qualité": {
        "fermiere":     {"label": "Viande fermière","termes": ["fermiere", "fermieres", "fermier", "fermiers"]},
        "label_rouge":  {"label": "Label Rouge",    "termes": ["label rouge"]},
        "bbc":          {"label": "Bleu Blanc Coeur","termes": ["bleu blanc coeur", "bbc"]},
        "vpf":          {"label": "VPF (Porc Français)", "termes": ["vpf"]},
        "vbf":          {"label": "VBF (Bovin Français)", "termes": ["vbf"]},
    },

    # ===== FROMAGES =====
    "Fromages": {
        "comte":        {"label": "Comté",          "termes": ["comte", "comtes"]},
        "emmental":     {"label": "Emmental",       "termes": ["emmental", "emmentals"]},
        "reblochon":    {"label": "Reblochon",      "termes": ["reblochon", "reblochons"]},
        "chevre":       {"label": "Chèvre",         "termes": ["chevre", "chevres"]},
        "camenbert":    {"label": "Camembert",      "termes": ["camenbert", "camenberts", "camembert", "camemberts"]},
        "bleu":         {"label": "Bleu",           "termes": ["bleu d'auvergne", "bleu de bresse", "bleu de gex", "fourme", "fourmes"]},
    },

    # ===== SAVEURS =====
    "Épices / Aromates": {
        "piment":       {"label": "Pimenté",        "termes": ["piment", "piments", "pimente", "pimentes"]},
        "paprika":      {"label": "Paprika",        "termes": ["paprika"]},
        "espelette":    {"label": "Espelette",      "termes": ["espelette", "espel"]},
        "poivres":      {"label": "Poivres",        "termes": ["poivre", "poivres"]},
        "thym":         {"label": "Thym",           "termes": ["thym", "thyms"]},
        "herbes":       {"label": "Aux herbes",     "termes": ["herbe", "herbes"]},
        "ail":          {"label": "Ail",            "termes": ["ail", "ails"]},
        "persillade":   {"label": "Persillade",     "termes": ["persillade", "persillades"]},
        "persillee":    {"label": "Persillée",      "termes": ["persillee", "persillees", "persille", "persilles"]},
    },

    "Garnitures / Accompagnements": {
        "oignons":      {"label": "Oignons",        "termes": ["oignon", "oignons"]},
        "echalote":     {"label": "Échalote",       "termes": ["echalote", "echalotes"]},
        "tomates":      {"label": "Tomates",        "termes": ["tomate", "tomates"]},
        "legumes":      {"label": "Légumes",        "termes": ["legume", "legumes"]},
        "mogette":      {"label": "Mogette",        "termes": ["mogette", "mogettes"]},
        "coco":         {"label": "Coco",           "termes": ["coco", "cocos"]},
        "pruneaux":     {"label": "Pruneaux",       "termes": ["pruneaux", "pruneau"]},
        "abricots":     {"label": "Abricots",       "termes": ["abricots", "abricot"]},
        "marrons":      {"label": "Marrons",        "termes": ["marron", "marrons"]},
        "raisins":      {"label": "Raisins",        "termes": ["raisin", "raisins"]},
        "citron":       {"label": "Citron",         "termes": ["citron", "citrons"]},
        "orange":       {"label": "Orange",         "termes": ["orange", "oranges"]},
        "melon":        {"label": "Melon",          "termes": ["melon"]},
        "muscadet":     {"label": "Muscadet",       "termes": ["muscadet", "muscadets"]},
        "biere":        {"label": "Bière",          "termes": ["biere", "bieres"]},
        "miel":         {"label": "Miel",           "termes": ["miel", "miels"]},
    },

    "Styles": {
        "nature":       {"label": "Nature",         "termes": ["nature", "natures", "nat"]},
        "naturel":      {"label": "Naturel",        "termes": ["naturel", "naturels", "naturelle", "naturelles"]},
        "trad":         {"label": "Traditionnelle", "termes": ["trad", "traditionnelle", "traditionnelles", "traditionnel", "traditionnels"]},
        "fine":         {"label": "Fine",           "termes": ["fine", "fines"]},
    },

    # ===== AUTRES =====
    "Autres": {
        "foie_gras":    {"label": "Foie gras",      "termes": ["foie gras"]},
        "magret":       {"label": "Magret",         "termes": ["magret", "magrets"]},
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
        # Requête 1 : catalogue + libellé produit + unite_fact (rapide, catalogue filtré par tiers)
        cursor.execute("""
            SELECT c.prod, p.libelle, p.unite_fact
            FROM catalogue c
            LEFT JOIN prod p ON c.prod = p.prod
            WHERE c.tiers = %s
        """, [code_tiers])
        catalogue_rows = cursor.fetchall()

        if not catalogue_rows:
            return []

        codes_produits = [r[0] for r in catalogue_rows]
        libelles = {r[0]: r[1] for r in catalogue_rows}
        unites_fact = {r[0]: r[2] for r in catalogue_rows}

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

        # Déterminer l'unité de vente depuis unite_fact de la table prod
        # 1 = unité, 2 = poids (kg)
        unite_fact = unites_fact.get(prod_code)
        if unite_fact == 1:
            unite = 'unité'
        elif unite_fact == 2:
            unite = 'kg'
        else:
            unite = 'unité'  # Par défaut

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

        # Tags basés sur l'unité de vente (unite_fact: 1=unité, 2=kg)
        if unite == 'kg':
            tags.append('kg')
        elif unite == 'unité':
            tags.append('unite')

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
