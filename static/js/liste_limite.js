/**
 * =============================================================================
 * LISTE_LIMITE.JS - Pagination responsive des listes
 * =============================================================================
 *
 * Ce module JavaScript limite le nombre d'éléments affichés dans les listes
 * selon la taille de l'écran, avec un bouton "Voir plus" pour charger la suite.
 *
 * Fonctionnalité :
 *   - Limite le nombre d'éléments visibles selon la largeur d'écran
 *   - Affiche un bouton "Voir plus" avec le nombre d'éléments restants
 *   - S'adapte automatiquement au redimensionnement de la fenêtre
 *
 * Seuils de limitation :
 *   - Petit écran (<768px)     : 20 éléments
 *   - Moyen écran (768-1199px) : 60 éléments
 *   - Grand écran (>=1200px)   : Tous les éléments (pas de limite)
 *
 * Utilisation HTML :
 *   <div data-liste-limitee>
 *     <div>Élément 1</div>
 *     <div>Élément 2</div>
 *     ...
 *   </div>
 *
 *   L'attribut data-liste-limitee active la fonctionnalité sur le conteneur.
 *   Fonctionne aussi avec les tableaux (<tbody data-liste-limitee>).
 *
 * Comportement :
 *   - Les éléments au-delà de la limite sont masqués avec display: none
 *   - Le bouton "Voir plus" affiche tous les éléments au clic
 *   - Le recalcul se fait automatiquement au redimensionnement
 *
 * Dépendances :
 *   - Bootstrap 5 (boutons et style)
 *   - Bootstrap Icons (bi-chevron-down)
 *
 * Projet : Extranet Giffaud Groupe
 * =============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
    // Récupération de tous les conteneurs avec l'attribut data-liste-limitee
    const conteneurs = document.querySelectorAll('[data-liste-limitee]');

    // Sortie si aucun conteneur à traiter
    if (!conteneurs.length) return;


    /**
     * Détermine la limite d'éléments à afficher selon la largeur d'écran.
     *
     * @returns {number} Nombre maximum d'éléments à afficher (Infinity = pas de limite)
     */
    function getLimite() {
        const w = window.innerWidth;
        if (w < 768) return 20;      // Mobile : 20 éléments
        if (w < 1200) return 60;     // Tablette : 60 éléments
        return Infinity;              // Desktop : tous
    }


    /**
     * Trouve l'élément parent approprié pour insérer le bouton "Voir plus".
     *
     * Pour un <tbody>, le bouton doit être inséré après la table (ou son
     * wrapper .table-responsive) plutôt qu'après le tbody lui-même.
     *
     * @param {HTMLElement} conteneur - Le conteneur avec data-liste-limitee
     * @returns {HTMLElement} L'élément après lequel insérer le bouton
     */
    function getInsertParent(conteneur) {
        if (conteneur.tagName === 'TBODY') {
            const table = conteneur.closest('table');
            const wrapper = table.closest('.table-responsive');
            return wrapper || table;
        }
        return conteneur;
    }


    /**
     * Applique la limite d'affichage sur tous les conteneurs.
     *
     * Cette fonction est appelée au chargement et à chaque redimensionnement.
     * Elle masque les éléments au-delà de la limite et gère le bouton
     * "Voir plus".
     */
    function appliquerLimite() {
        const limite = getLimite();

        conteneurs.forEach(conteneur => {
            // Récupération des enfants (en excluant le wrapper du bouton)
            const items = Array.from(conteneur.children).filter(
                el => !el.classList.contains('voir-plus-wrapper')
            );
            let nbCaches = 0;

            // Masquage/affichage des éléments selon la limite
            for (let i = 0; i < items.length; i++) {
                if (i < limite) {
                    // Afficher l'élément
                    items[i].style.removeProperty('display');
                } else {
                    // Masquer l'élément (!important pour surcharger d'autres styles)
                    items[i].style.setProperty('display', 'none', 'important');
                    nbCaches++;
                }
            }

            // Gestion du bouton "Voir plus"
            const insertParent = getInsertParent(conteneur);
            let btn = insertParent.parentElement.querySelector('.voir-plus-wrapper');

            if (nbCaches > 0) {
                // Création ou mise à jour du bouton
                if (!btn) {
                    btn = document.createElement('div');
                    btn.className = 'voir-plus-wrapper text-center mt-3 mb-4';
                    btn.innerHTML = '<button class="btn btn-outline-primary btn-voir-plus"><i class="bi bi-chevron-down"></i> Voir plus (' + nbCaches + ' restants)</button>';
                    insertParent.parentElement.insertBefore(btn, insertParent.nextSibling);

                    // Événement clic pour afficher tous les éléments
                    btn.querySelector('.btn-voir-plus').addEventListener('click', () => {
                        for (let i = 0; i < items.length; i++) {
                            items[i].style.removeProperty('display');
                        }
                        btn.remove();
                    });
                } else {
                    // Mise à jour du texte du bouton existant
                    btn.querySelector('.btn-voir-plus').innerHTML = '<i class="bi bi-chevron-down"></i> Voir plus (' + nbCaches + ' restants)';
                }
            } else if (btn) {
                // Suppression du bouton si tous les éléments sont affichés
                btn.remove();
            }
        });
    }

    // Application initiale de la limite
    appliquerLimite();

    // Recalcul au redimensionnement de la fenêtre
    window.addEventListener('resize', appliquerLimite);
});
