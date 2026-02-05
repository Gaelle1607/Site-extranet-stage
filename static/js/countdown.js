/**
 * =============================================================================
 * COUNTDOWN.JS - Compte à rebours pour les éléments restaurables
 * =============================================================================
 *
 * Ce module JavaScript gère les comptes à rebours affichés sur le dashboard
 * administrateur pour les éléments supprimés qui sont encore restaurables.
 *
 * Fonctionnalité :
 *   - Affiche un compteur dégressif (mm:ss) pour chaque élément
 *   - Met à jour toutes les secondes automatiquement
 *   - Recharge la page quand un compteur atteint 0
 *
 * Utilisation HTML :
 *   <span data-countdown="300">
 *     <span class="countdown-time">5:00</span>
 *   </span>
 *
 * Attributs :
 *   - data-countdown : Nombre de secondes restantes (décrémenté à chaque tick)
 *   - .countdown-time : Élément affichant le temps formaté
 *
 * Contexte métier :
 *   Les utilisateurs et commandes supprimés peuvent être restaurés pendant
 *   une période de 5 minutes (300 secondes). Ce compteur montre le temps
 *   restant avant la suppression définitive automatique.
 *
 * Projet : Extranet Giffaud Groupe
 * =============================================================================
 */

document.addEventListener('DOMContentLoaded', function() {

    /**
     * Met à jour tous les comptes à rebours présents sur la page.
     *
     * Pour chaque élément avec l'attribut data-countdown :
     * 1. Récupère le nombre de secondes restantes
     * 2. Formate en minutes:secondes (ex: 4:32)
     * 3. Affiche dans l'élément .countdown-time
     * 4. Décrémente le compteur de 1 seconde
     *
     * Si un compteur atteint 0, recharge la page pour mettre à jour
     * l'affichage (les éléments expirés disparaissent de la liste).
     */
    function updateCountdowns() {
        const countdowns = document.querySelectorAll('[data-countdown]');
        countdowns.forEach(function(element) {
            let seconds = parseInt(element.getAttribute('data-countdown'));
            const timeSpan = element.querySelector('.countdown-time');

            if (seconds <= 0) {
                // Recharger la page pour mettre à jour l'affichage
                location.reload();
                return;
            }

            // Formatage mm:ss avec padding des secondes
            const minutes = Math.floor(seconds / 60);
            const secs = seconds % 60;
            timeSpan.textContent = minutes + ':' + (secs < 10 ? '0' : '') + secs;

            // Décrémenter pour le prochain tick
            element.setAttribute('data-countdown', seconds - 1);
        });
    }

    // Mettre à jour immédiatement puis toutes les secondes
    updateCountdowns();
    setInterval(updateCountdowns, 1000);
});
