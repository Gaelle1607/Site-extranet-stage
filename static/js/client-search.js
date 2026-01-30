/**
 * Recherche de clients pour le formulaire d'inscription
 * Nécessite l'URL de l'API en data-attribute sur le formulaire
 */
function initClientSearch(apiUrl) {
    const searchInput = document.getElementById('client-search');
    const hiddenInput = document.getElementById('client');
    const resultsDiv = document.getElementById('search-results');
    const selectedDiv = document.getElementById('selected-client');

    if (!searchInput || !hiddenInput || !resultsDiv || !selectedDiv) {
        return;
    }

    let debounceTimer;

    // Pré-remplissage depuis le cadencier
    if (hiddenInput.value && searchInput.value) {
        selectedDiv.innerHTML = `<span class="badge bg-success"><i class="bi bi-check"></i> ${searchInput.value} (${hiddenInput.value})</span>`;
    }

    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();

        if (query.length < 2) {
            resultsDiv.innerHTML = '';
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`${apiUrl}?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    resultsDiv.innerHTML = '';
                    if (data.clients.length === 0) {
                        resultsDiv.innerHTML = '<div class="list-group-item text-muted">Aucun client trouvé</div>';
                        return;
                    }
                    data.clients.forEach(client => {
                        const item = document.createElement('a');
                        item.href = '#';
                        item.className = 'list-group-item list-group-item-action';
                        item.innerHTML = `<strong>${client.nom}</strong> <small class="text-muted">(${client.tiers})</small>`;
                        item.addEventListener('click', function(e) {
                            e.preventDefault();
                            hiddenInput.value = client.tiers;
                            searchInput.value = client.nom;
                            selectedDiv.innerHTML = `<span class="badge bg-success"><i class="bi bi-check"></i> ${client.nom} (${client.tiers})</span>`;
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

    // Fermer les résultats si on clique ailleurs
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
            resultsDiv.innerHTML = '';
        }
    });
}
