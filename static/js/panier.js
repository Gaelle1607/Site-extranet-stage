/**
 * =============================================================================
 * PANIER.JS - Gestion du panier d'achat
 * =============================================================================
 *
 * Ce module JavaScript gère toutes les interactions liées au panier d'achat
 * de l'application Extranet Giffaud Groupe.
 *
 * Fonctionnalités principales :
 *   - Ajout de produits au panier (AJAX)
 *   - Modification des quantités avec debounce
 *   - Suppression d'articles (avec confirmation)
 *   - Mise à jour dynamique du récapitulatif latéral
 *   - Notifications utilisateur (toasts Bootstrap)
 *   - Restauration de la position de scroll après rechargement
 *
 * Architecture :
 *   - Toutes les requêtes sont effectuées en AJAX pour éviter le rechargement
 *   - Le header X-Requested-With identifie les requêtes AJAX côté serveur
 *   - Le badge du panier et les totaux sont mis à jour dynamiquement
 *
 * Dépendances :
 *   - Bootstrap 5 (pour les alertes et le style)
 *   - Bootstrap Icons (pour les icônes)
 *
 * Projet : Extranet Giffaud Groupe
 * =============================================================================
 */

document.addEventListener('DOMContentLoaded', function() {

    // =========================================================================
    // RESTAURATION DE LA POSITION DE SCROLL
    // =========================================================================
    // Après un rechargement de page, restaure la position de scroll
    // stockée en session storage pour améliorer l'expérience utilisateur
    const savedScrollPos = sessionStorage.getItem('scrollPos');
    if (savedScrollPos) {
        window.scrollTo(0, parseInt(savedScrollPos));
        sessionStorage.removeItem('scrollPos');
    }

    // =========================================================================
    // AJOUT AU PANIER EN AJAX
    // =========================================================================
    // Intercepte la soumission des formulaires d'ajout au panier
    // pour les traiter en AJAX sans rechargement de page
    document.querySelectorAll('.ajouter-panier-form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // Indicateur de chargement sur le bouton
            const btn = form.querySelector('button[type="submit"]');
            const originalContent = btn.innerHTML;
            btn.classList.add('loading');
            btn.disabled = true;

            // Envoi de la requête AJAX
            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Restauration du bouton
                btn.innerHTML = originalContent;
                btn.classList.remove('loading');
                btn.disabled = false;

                if (data.success) {
                    // Mise à jour du badge du panier
                    updatePanierBadge(data.panier_count);

                    // Mise à jour du récap panier (sur la page catalogue)
                    if (data.lignes_panier) {
                        updateRecapPanier(data.lignes_panier, data.total_panier);
                    }

                    // Notification de succès
                    showNotification(data.message, 'success');
                } else {
                    // Notification d'erreur (stock insuffisant, etc.)
                    showNotification(data.message, 'warning');
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

    // =========================================================================
    // MODIFICATION DE QUANTITÉ AVEC DEBOUNCE
    // =========================================================================
    // Écoute les changements sur les champs de quantité
    // Le debounce de 500ms évite les requêtes multiples pendant la saisie
    document.querySelectorAll('.quantite-input').forEach(function(input) {
        let timeout;
        input.addEventListener('change', function() {
            clearTimeout(timeout);

            timeout = setTimeout(() => {
                const form = input.closest('form');

                // Récupérer le stock max depuis l'attribut data-stock de l'input
                const stockMax = input.dataset.stock ? parseInt(input.dataset.stock) : Infinity;

                let quantiteSaisie = parseInt(input.value);

                // Vérifier si la quantité dépasse le stock
                if (stockMax !== Infinity && quantiteSaisie > stockMax) {
                    quantiteSaisie = stockMax;
                    input.value = stockMax;
                    showNotification('Quantité maximale disponible : ' + stockMax, 'warning');
                }

                // Soumettre le formulaire avec la quantité corrigée
                submitQuantiteForm(form);
            }, 500);
        });
    });


    // =========================================================================
    // SUPPRESSION D'ARTICLE (PAGE PANIER)
    // =========================================================================
    // Gère la suppression d'articles depuis la page panier avec confirmation
    document.querySelectorAll('.supprimer-ligne-form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // Confirmation avant suppression
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

    // =========================================================================
    // DATE DE LIVRAISON MINIMUM
    // =========================================================================
    // Configure la date minimum de livraison à aujourd'hui + 7 jours
    const dateLivraison = document.getElementById('date-livraison');
    if (dateLivraison) {
        const today = new Date();
        today.setDate(today.getDate() + 7);
        const minDate = today.toISOString().split('T')[0];
        dateLivraison.min = minDate;
        dateLivraison.value = minDate;
    }
});


/**
 * Soumet le formulaire de modification de quantité en AJAX.
 *
 * Cette fonction envoie la nouvelle quantité au serveur et met à jour
 * l'interface utilisateur avec les nouveaux totaux.
 *
 * @param {HTMLFormElement} form - Le formulaire contenant les données
 */
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


/**
 * Met à jour le badge du nombre d'articles dans la navbar.
 *
 * Gère l'affichage du badge rouge avec animation de rebond.
 * Crée le badge s'il n'existe pas, le supprime si le panier est vide.
 *
 * @param {number} count - Nombre d'articles dans le panier
 */
function updatePanierBadge(count) {
    const badge = document.getElementById('panier-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            // Animation de rebond pour attirer l'attention
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


/**
 * Met à jour l'affichage du total du panier.
 *
 * @param {number} total - Montant total du panier en euros
 */
function updatePanierTotal(total) {
    const totalElement = document.querySelector('.panier-total');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2) + ' €';
    }
}


/**
 * Met à jour le compteur d'articles dans le récapitulatif.
 *
 * @param {number} count - Nombre d'articles
 */
function updateNombreArticles(count) {
    // Mettre à jour le nombre d'articles dans le récapitulatif de la page panier
    const articlesElements = document.querySelectorAll('.card-body .d-flex.justify-content-between.mb-2 span:last-child');
    articlesElements.forEach(el => {
        if (el.previousElementSibling && el.previousElementSibling.textContent === 'Articles') {
            el.textContent = count;
        }
    });
}


/**
 * Reconstruit le récapitulatif du panier dans le bandeau latéral.
 *
 * Génère dynamiquement le HTML avec les lignes de produits,
 * le total et les boutons d'action.
 *
 * @param {Array} lignes - Tableau des lignes du panier
 * @param {number} total - Total du panier
 */
function updateRecapPanier(lignes, total) {
    const recapContainer = document.getElementById('recap-panier-content');
    if (!recapContainer) return;

    if (lignes && lignes.length > 0) {
        let html = '<div class="list-group list-group-flush mb-3">';
        lignes.forEach(ligne => {
            html += `
                <div class="list-group-item px-0">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="flex-grow-1">
                            <small class="fw-bold">${ligne.nom}</small>
                            <br>
                            <small class="text-muted">${ligne.quantite} x ${ligne.prix.toFixed(2)} €</small>
                        </div>
                        <div class="d-flex flex-column align-items-center">
                            <span class="badge btn-success" style="white-space: nowrap; pointer-events: none;">${ligne.total.toFixed(2)} €</span>
                            <form method="post" action="/commandes/panier/supprimer/" class="supprimer-recap-form" style="margin: 0;">
                                <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRFToken()}">
                                <input type="hidden" name="reference" value="${ligne.reference}">
                                <button type="submit" class="btn btn-link text-danger p-0 mt-1" title="Supprimer">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        html += '<hr>';
        html += `
            <div class="d-flex flex-row flex-md-column flex-lg-row justify-content-between align-items-center mb-3">
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


/**
 * Récupère le token CSRF pour les requêtes AJAX.
 *
 * Cherche d'abord dans les inputs hidden du formulaire,
 * puis dans les cookies en fallback.
 *
 * @returns {string} Le token CSRF ou chaîne vide
 */
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


/**
 * Attache les événements de suppression aux formulaires du récapitulatif.
 *
 * Cette fonction doit être appelée après chaque mise à jour du DOM
 * du récapitulatif pour réattacher les listeners aux nouveaux éléments.
 */
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


/**
 * Affiche une notification toast à l'utilisateur.
 *
 * La notification apparaît en haut à droite de l'écran et disparaît
 * automatiquement après 3 secondes. Une seule notification est
 * affichée à la fois.
 *
 * @param {string} message - Message à afficher
 * @param {string} type - Type Bootstrap : 'success', 'danger', 'warning', 'info'
 */
function showNotification(message, type) {
    // Vérifie si une notification existe déjà et la supprime
    const existingAlert = document.querySelector('.alert.position-fixed');
    if (existingAlert){
        existingAlert.remove();
    }

    // Créer une notification toast
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
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
