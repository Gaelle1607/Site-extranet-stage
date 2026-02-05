/**
 * =============================================================================
 * ACCORDION-FILTRES.JS - Ouverture automatique des filtres actifs
 * =============================================================================
 *
 * Ce module JavaScript gère l'état d'ouverture des accordéons de filtres
 * dans le catalogue produits et les recommandations.
 *
 * Fonctionnalité :
 *   Ouvre automatiquement les groupes d'accordéon qui contiennent
 *   des filtres actuellement cochés (sélectionnés).
 *
 * Comportement :
 *   - Parcourt tous les groupes d'accordéon
 *   - Détecte ceux qui ont au moins une checkbox cochée
 *   - Les ouvre en ajoutant la classe 'show' au collapse
 *   - Met à jour l'état du bouton accordéon (aria-expanded)
 *
 * Utilisation :
 *   Ce script s'initialise automatiquement au chargement du DOM.
 *   Il cible spécifiquement l'élément #accordionFiltres.
 *
 * Structure HTML attendue :
 *   <div id="accordionFiltres">
 *     <div class="accordion-item">
 *       <button class="accordion-button collapsed">...</button>
 *       <div class="accordion-collapse">
 *         <input type="checkbox" checked>
 *       </div>
 *     </div>
 *   </div>
 *
 * Dépendances :
 *   - Bootstrap 5 (accordéon)
 *
 * Projet : Extranet Giffaud Groupe
 * =============================================================================
 */


/**
 * Initialise l'ouverture automatique des accordéons avec filtres actifs.
 *
 * Cette fonction améliore l'expérience utilisateur en ouvrant les groupes
 * de filtres qui ont des options sélectionnées, permettant à l'utilisateur
 * de voir immédiatement ses filtres actifs sans avoir à les ouvrir manuellement.
 */
function initAccordionFiltres() {
    // Parcours de tous les groupes d'accordéon
    document.querySelectorAll('#accordionFiltres .accordion-item').forEach(function(item) {
        // Vérification si le groupe contient une checkbox cochée
        if (item.querySelector('input[type="checkbox"]:checked')) {
            // Récupération des éléments de l'accordéon
            var collapse = item.querySelector('.accordion-collapse');
            var btn = item.querySelector('.accordion-button');

            // Ouverture du groupe
            collapse.classList.add('show');

            // Mise à jour de l'état du bouton
            btn.classList.remove('collapsed');
            btn.setAttribute('aria-expanded', 'true');
        }
    });
}


// Auto-initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', initAccordionFiltres);
