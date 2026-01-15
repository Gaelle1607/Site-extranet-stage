// Extranet B2B - JavaScript pour le panier

document.addEventListener('DOMContentLoaded', function() {

    // Restaurer la position de scroll après rechargement
    const savedScrollPos = sessionStorage.getItem('scrollPos');
    if (savedScrollPos) {
        window.scrollTo(0, parseInt(savedScrollPos));
        sessionStorage.removeItem('scrollPos');
    }

    // Ajout au panier en AJAX
    document.querySelectorAll('.ajouter-panier-form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const btn = form.querySelector('button[type="submit"]');
            const originalContent = btn.innerHTML;
            btn.classList.add('loading');
            btn.disabled = true;

            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                btn.innerHTML = originalContent;
                btn.classList.remove('loading');
                btn.disabled = false;

                if (data.success) {
                    // Mettre à jour le badge du panier
                    updatePanierBadge(data.panier_count);

                    // Mettre à jour le récap panier (sur la page catalogue)
                    if (data.lignes_panier) {
                        updateRecapPanier(data.lignes_panier, data.total_panier);
                    }

                    // Notification de succès
                    showNotification(data.message, 'success');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                btn.innerHTML = originalContent;
                btn.classList.remove('loading');
                btn.disabled = false;
                showNotification('Une erreur est survenue', 'danger');
            });
        });
    });

    // Modification quantité panier
    document.querySelectorAll('.quantite-input').forEach(function(input) {
        let timeout;
        input.addEventListener('change', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const form = input.closest('form');
                submitQuantiteForm(form);
            }, 500);
        });
    });

    // Suppression du panier (page panier)
    document.querySelectorAll('.supprimer-ligne-form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            if (!confirm('Supprimer cet article ?')) return;

            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Supprimer la ligne du tableau
                    const row = form.closest('tr');
                    row.remove();

                    // Mettre à jour les totaux
                    updatePanierBadge(data.panier_count);
                    updatePanierTotal(data.total_panier);
                    updateNombreArticles(data.panier_count);

                    // Mettre à jour le récap panier aussi
                    if (data.lignes_panier) {
                        updateRecapPanier(data.lignes_panier, data.total_panier);
                    }

                    showNotification(data.message, 'success');

                    // Si panier vide, recharger la page
                    if (data.panier_count === 0) {
                        location.reload();
                    }
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showNotification('Une erreur est survenue', 'danger');
            });
        });
    });

    // Attacher les listeners pour le récap panier (page catalogue)
    attachSupprimerRecapListeners();
});

function submitQuantiteForm(form) {
    fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mettre à jour le total de la ligne
            const row = form.closest('tr');
            if (row) {
                const totalCell = row.querySelector('.ligne-total');
                if (totalCell && data.total_ligne !== undefined) {
                    totalCell.textContent = data.total_ligne.toFixed(2) + ' €';
                }
            }

            // Mettre à jour les totaux
            updatePanierBadge(data.panier_count);
            updatePanierTotal(data.total_panier);
            updateNombreArticles(data.panier_count);

            // Si quantité 0, supprimer la ligne
            const quantiteInput = form.querySelector('.quantite-input');
            if (quantiteInput && parseInt(quantiteInput.value) <= 0) {
                row.remove();
                if (data.panier_count === 0) {
                    location.reload();
                }
            }
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
    });
}

function updatePanierBadge(count) {
    const badge = document.getElementById('panier-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.classList.add('cart-bounce');
            setTimeout(() => badge.classList.remove('cart-bounce'), 300);
        } else {
            badge.remove();
        }
    } else if (count > 0) {
        // Créer le badge s'il n'existe pas
        const panierLink = document.querySelector('a[href*="panier"]');
        if (panierLink) {
            const newBadge = document.createElement('span');
            newBadge.id = 'panier-badge';
            newBadge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger';
            newBadge.textContent = count;
            panierLink.appendChild(newBadge);
        }
    }
}

function updatePanierTotal(total) {
    const totalElement = document.querySelector('.panier-total');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2) + ' €';
    }
}

function updateNombreArticles(count) {
    // Mettre à jour le nombre d'articles dans le récapitulatif de la page panier
    const articlesElements = document.querySelectorAll('.card-body .d-flex.justify-content-between.mb-2 span:last-child');
    articlesElements.forEach(el => {
        if (el.previousElementSibling && el.previousElementSibling.textContent === 'Articles') {
            el.textContent = count;
        }
    });
}

function updateRecapPanier(lignes, total) {
    const recapContainer = document.getElementById('recap-panier-content');
    if (!recapContainer) return;

    if (lignes && lignes.length > 0) {
        let html = '<div class="list-group list-group-flush mb-3">';
        lignes.forEach(ligne => {
            html += `
                <div class="list-group-item px-0">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <small class="fw-bold">${ligne.nom}</small>
                            <br>
                            <small class="text-muted">${ligne.quantite} x ${ligne.prix.toFixed(2)} €</small>
                        </div>
                        <span class="badge recap-prix-badge me-2">${ligne.total.toFixed(2)} €</span>
                        <form method="post" action="/commandes/panier/supprimer/" class="supprimer-recap-form">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRFToken()}">
                            <input type="hidden" name="reference" value="${ligne.reference}">
                            <button type="submit" class="btn btn-link text-danger p-0" title="Supprimer">
                                <i class="bi bi-trash"></i>
                            </button>
                        </form>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        html += '<hr>';
        html += `
            <div class="d-flex justify-content-between mb-3">
                <span class="fw-bold">Total HT</span>
                <span class="fw-bold h5 mb-0">${total.toFixed(2)} €</span>
            </div>
            <div class="d-grid gap-2">
                <a href="/commandes/panier/" class="btn btn-outline-primary">
                    <i class="bi bi-pencil"></i> Modifier
                </a>
                <a href="/commandes/valider/" class="btn btn-success">
                    <i class="bi bi-check2-circle"></i> Commander
                </a>
            </div>
        `;
        recapContainer.innerHTML = html;

        // Réattacher les event listeners aux nouveaux boutons supprimer
        attachSupprimerRecapListeners();
    } else {
        recapContainer.innerHTML = `
            <div class="text-center py-3">
                <i class="bi bi-cart-x text-muted" style="font-size: 2rem;"></i>
                <p class="text-muted mt-2 mb-0">Panier vide</p>
            </div>
        `;
    }
}

function getCSRFToken() {
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) return csrfInput.value;

    // Fallback: chercher dans les cookies
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') return value;
    }
    return '';
}

function attachSupprimerRecapListeners() {
    document.querySelectorAll('.supprimer-recap-form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Mettre à jour le badge du panier
                    updatePanierBadge(data.panier_count);

                    // Reconstruire le récap panier
                    if (data.panier_count === 0) {
                        updateRecapPanier([], 0);
                    } else {
                        // Supprimer la ligne du récap
                        const listItem = form.closest('.list-group-item');
                        if (listItem) listItem.remove();

                        // Mettre à jour le total affiché
                        const totalElement = document.querySelector('#recap-panier-content .h5.mb-0');
                        if (totalElement) {
                            totalElement.textContent = data.total_panier.toFixed(2) + ' €';
                        }
                    }

                    showNotification(data.message, 'success');
                } else {
                    showNotification(data.message || 'Une erreur est survenue', 'danger');
                    console.error('Erreur serveur:', data);
                }
            })
            .catch(error => {
                console.error('Erreur fetch:', error);
                showNotification('Une erreur est survenue', 'danger');
            });
        });
    });
}

function showNotification(message, type) {
    // Créer une notification toast
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alert);

    // Auto-fermeture après 3 secondes
    setTimeout(() => {
        alert.remove();
    }, 3000);
}
