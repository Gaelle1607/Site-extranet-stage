/**
 * Calcul automatique de la date de départ des camions
 * Date départ = Date livraison - 2 jours
 */
function initDateCalcul() {
    const dateLivraison = document.getElementById('date-livraison');
    const dateDepartCamions = document.getElementById('date-depart-camions');

    if (!dateLivraison || !dateDepartCamions) {
        return;
    }

    function calculerDateDepart() {
        if (dateLivraison.value) {
            const date = new Date(dateLivraison.value);
            date.setDate(date.getDate() - 2);
            dateDepartCamions.value = date.toISOString().split('T')[0];
        } else {
            dateDepartCamions.value = '';
        }
    }

    dateLivraison.addEventListener('change', calculerDateDepart);
    // Calculer au chargement si une date existe déjà
    calculerDateDepart();
}

// Auto-init au chargement du DOM
document.addEventListener('DOMContentLoaded', initDateCalcul);
