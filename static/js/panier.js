// Extranet B2B - JavaScript pour le panier

document.addEventListener('DOMContentLoaded', function() {

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
                if (data.success) {
                    // Mettre à jour le badge du panier
                    updatePanierBadge(data.panier_count);

                    // Afficher notification
                    showNotification(data.message, 'success');

                    // Animation du bouton
                    btn.innerHTML = '<i class="bi bi-check"></i>';
                    setTimeout(() => {
                        btn.innerHTML = originalContent;
                        btn.classList.remove('loading');
                        btn.disabled = false;
                    }, 1000);
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

    // Suppression du panier
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
                if (totalCell && data.total_ligne) {
                    totalCell.textContent = data.total_ligne.toFixed(2) + ' €';
                }
            }

            // Mettre à jour les totaux
            updatePanierBadge(data.panier_count);
            updatePanierTotal(data.total_panier);

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

function showNotification(message, type) {
    // Créer une notification toast
    const container = document.querySelector('.container');
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
