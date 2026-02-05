/**
 * =============================================================================
 * DATE-CALCUL.JS - Calcul automatique de la date de départ
 * =============================================================================
 *
 * Ce module JavaScript calcule automatiquement la date de départ des camions
 * en fonction de la date de livraison sélectionnée par l'utilisateur.
 *
 * Logique métier :
 *   Date de départ = Date de livraison - 2 jours
 *
 * Utilisation :
 *   Ce script s'initialise automatiquement au chargement du DOM si les
 *   éléments requis sont présents sur la page.
 *
 * Éléments HTML requis :
 *   - #date-livraison : Champ input de type date pour la livraison
 *   - #date-depart-camions : Champ input de type date pour le départ
 *
 * Comportement :
 *   - Calcul au changement de la date de livraison
 *   - Calcul initial si une date est pré-remplie
 *   - Effacement de la date de départ si pas de date de livraison
 *
 * Note :
 *   Ce script est une version réutilisable de la logique présente dans
 *   commander.js. Il peut être inclus sur d'autres pages qui nécessitent
 *   ce calcul (ex: formulaires d'administration).
 *
 * Projet : Extranet Giffaud Groupe
 * =============================================================================
 */


/**
 * Initialise le calcul automatique de la date de départ.
 *
 * Configure l'événement change sur le champ de date de livraison
 * et effectue un calcul initial si une date est déjà présente.
 */
function initDateCalcul() {
    const dateLivraison = document.getElementById('date-livraison');
    const dateDepartCamions = document.getElementById('date-depart-camions');

    // Sortie si les éléments ne sont pas présents sur la page
    if (!dateLivraison || !dateDepartCamions) {
        return;
    }

    /**
     * Calcule et affiche la date de départ des camions.
     *
     * La date de départ est fixée à 2 jours avant la date de livraison
     * pour tenir compte des délais de préparation et de transport.
     */
    function calculerDateDepart() {
        if (dateLivraison.value) {
            // Création d'un objet Date à partir de la valeur sélectionnée
            const date = new Date(dateLivraison.value);
            // Soustraction de 2 jours
            date.setDate(date.getDate() - 2);
            // Formatage en YYYY-MM-DD pour l'input date
            dateDepartCamions.value = date.toISOString().split('T')[0];
        } else {
            // Effacement si pas de date de livraison
            dateDepartCamions.value = '';
        }
    }

    // Écouteur sur le changement de date de livraison
    dateLivraison.addEventListener('change', calculerDateDepart);

    // Calcul initial au chargement si une date existe déjà
    calculerDateDepart();
}


// Auto-initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', initDateCalcul);
