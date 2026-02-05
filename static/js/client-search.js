/**
 * =============================================================================
 * CLIENT-SEARCH.JS - Recherche de clients avec autocomplétion
 * =============================================================================
 *
 * Ce module JavaScript fournit une fonctionnalité de recherche de clients
 * avec autocomplétion pour le formulaire d'inscription administrateur.
 *
 * Fonctionnalités :
 *   - Recherche en temps réel avec debounce (300ms)
 *   - Affichage des résultats dans une liste déroulante
 *   - Sélection d'un client et stockage du code tiers
 *   - Fermeture automatique des résultats au clic extérieur
 *   - Pré-remplissage possible depuis le cadencier
 *
 * Éléments HTML requis :
 *   - #client-search : Champ de saisie pour la recherche
 *   - #client : Champ hidden pour stocker le code tiers
 *   - #search-results : Conteneur pour les résultats
 *   - #selected-client : Zone d'affichage du client sélectionné
 *
 * API attendue :
 *   GET {apiUrl}?q={recherche}
 *   Réponse : { clients: [{ nom: string, tiers: number }, ...] }
 *
 * Utilisation :
 *   initClientSearch('/administration/api/recherche-clients/');
 *
 * Dépendances :
 *   - Bootstrap 5 (pour le style des list-group)
 *   - Bootstrap Icons (bi-check)
 *
 * Projet : Extranet Giffaud Groupe
 * =============================================================================
 */


/**
 * Initialise la recherche de clients avec autocomplétion.
 *
 * Cette fonction configure tous les événements nécessaires pour la
 * recherche interactive de clients. Elle doit être appelée au chargement
 * de la page avec l'URL de l'API comme paramètre.
 *
 * @param {string} apiUrl - URL de l'API de recherche de clients
 *
 * @example
 * // Dans le template HTML :
 * <script>
 *   initClientSearch('{% url "administration:recherche_clients_api" %}');
 * </script>
 */
function initClientSearch(apiUrl) {
    // Récupération des éléments du DOM
    const searchInput = document.getElementById('client-search');
    const hiddenInput = document.getElementById('client');
    const resultsDiv = document.getElementById('search-results');
    const selectedDiv = document.getElementById('selected-client');

    // Vérification que tous les éléments requis existent
    if (!searchInput || !hiddenInput || !resultsDiv || !selectedDiv) {
        return;
    }

    // Timer pour le debounce des requêtes
    let debounceTimer;

    // =========================================================================
    // PRÉ-REMPLISSAGE DEPUIS LE CADENCIER
    // =========================================================================
    // Si un client est déjà sélectionné (navigation depuis le cadencier),
    // afficher le badge de confirmation
    if (hiddenInput.value && searchInput.value) {
        selectedDiv.innerHTML = `<span class="badge bg-success"><i class="bi bi-check"></i> ${searchInput.value} (${hiddenInput.value})</span>`;
    }

    // =========================================================================
    // RECHERCHE EN TEMPS RÉEL
    // =========================================================================
    searchInput.addEventListener('input', function() {
        // Annulation de la requête précédente en attente
        clearTimeout(debounceTimer);
        const query = this.value.trim();

        // Minimum 2 caractères pour lancer la recherche
        if (query.length < 2) {
            resultsDiv.innerHTML = '';
            return;
        }

        // Debounce de 300ms pour éviter les requêtes à chaque frappe
        debounceTimer = setTimeout(() => {
            fetch(`${apiUrl}?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    resultsDiv.innerHTML = '';

                    // Affichage si aucun résultat
                    if (data.clients.length === 0) {
                        resultsDiv.innerHTML = '<div class="list-group-item text-muted">Aucun client trouvé</div>';
                        return;
                    }

                    // Construction de la liste des résultats
                    data.clients.forEach(client => {
                        const item = document.createElement('a');
                        item.href = '#';
                        item.className = 'list-group-item list-group-item-action';
                        item.innerHTML = `<strong>${client.nom}</strong> <small class="text-muted">(${client.tiers})</small>`;

                        // Gestion de la sélection d'un client
                        item.addEventListener('click', function(e) {
                            e.preventDefault();
                            // Stockage du code tiers dans le champ hidden
                            hiddenInput.value = client.tiers;
                            // Affichage du nom dans le champ de recherche
                            searchInput.value = client.nom;
                            // Badge de confirmation
                            selectedDiv.innerHTML = `<span class="badge bg-success"><i class="bi bi-check"></i> ${client.nom} (${client.tiers})</span>`;
                            // Fermeture des résultats
                            resultsDiv.innerHTML = '';
                        });

                        resultsDiv.appendChild(item);
                    });
                })
                .catch(error => {
                    console.error('Erreur:', error);
                    resultsDiv.innerHTML = '<div class="list-group-item text-danger">Erreur de recherche</div>';
                });
        }, 300);
    });

    // =========================================================================
    // FERMETURE AU CLIC EXTÉRIEUR
    // =========================================================================
    // Ferme la liste des résultats si on clique en dehors
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
            resultsDiv.innerHTML = '';
        }
    });
}
