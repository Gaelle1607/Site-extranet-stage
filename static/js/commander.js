// Extranet B2B - JavaScript pour la page de passage de commande

document.addEventListener('DOMContentLoaded', () => {

    // Calcul automatique de la date de départ des camions (2 jours avant livraison)
    // Placé en premier pour s'assurer qu'il s'exécute même si le reste échoue
    const dateLivraison = document.getElementById('date-livraison');
    const dateDepartCamions = document.getElementById('date-depart-camions');

    function calculerDateDepart() {
        if (dateLivraison && dateLivraison.value) {
            const date = new Date(dateLivraison.value);
            date.setDate(date.getDate() - 2);
            dateDepartCamions.value = date.toISOString().split('T')[0];
        } else if (dateDepartCamions) {
            dateDepartCamions.value = '';
        }
    }

    if (dateLivraison && dateDepartCamions) {
        dateLivraison.addEventListener('change', calculerDateDepart);
        // Calculer au chargement si une date existe déjà
        calculerDateDepart();
    }

    // Recherche produits en temps réel
    const rechercheInput = document.getElementById('recherche-produit');
    const effacerBtn = document.getElementById('effacer-recherche');
    const lignesProduits = document.querySelectorAll('.produit-ligne');

    if (!rechercheInput) return; // Sortir si pas d'éléments de recherche

    // Empêcher Entrée de soumettre le formulaire
    rechercheInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') e.preventDefault();
    });

    function filtrerProduits() {
        const query = rechercheInput.value.toLowerCase();
        effacerBtn.style.display = query ? '' : 'none';
        lignesProduits.forEach(ligne => {
            const nom = ligne.querySelector('.produit-nom').textContent.toLowerCase();
            if (nom.includes(query)) {
                ligne.style.removeProperty('display');
            } else {
                ligne.style.setProperty('display', 'none', 'important');
            }
        });
    }

    rechercheInput.addEventListener('input', filtrerProduits);

    effacerBtn.addEventListener('click', () => {
        rechercheInput.value = '';
        filtrerProduits();
        rechercheInput.focus();
    });

    // CSRF token pour les requêtes AJAX
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Synchroniser la quantité avec le panier en session
    const syncTimers = {};
    function syncPanier(reference, quantite) {
        // Debounce par référence pour éviter trop de requêtes
        clearTimeout(syncTimers[reference]);
        syncTimers[reference] = setTimeout(() => {
            const formData = new FormData();
            formData.append('reference', reference);
            formData.append('quantite', quantite);
            fetch('/commandes/panier/modifier/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                },
                body: formData,
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    // Mettre à jour le badge panier dans la navbar
                    let badge = document.getElementById('panier-badge');
                    if (data.panier_count > 0) {
                        if (!badge) {
                            // Créer le badge s'il n'existe pas
                            const panierLink = document.querySelector('a[href*="panier"]');
                            if (panierLink) {
                                badge = document.createElement('span');
                                badge.id = 'panier-badge';
                                badge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill';
                                panierLink.appendChild(badge);
                            }
                        }
                        if (badge) badge.textContent = data.panier_count;
                    } else if (badge) {
                        badge.remove();
                    }
                }
            });
        }, 400);
    }

    // Calcul des totaux
    const inputs = document.querySelectorAll('.quantite-commande-input');

    inputs.forEach(input => {
        input.addEventListener('input', () => {
            const prix = parseFloat(input.dataset.prix) || 0;
            const quantite = parseInt(input.value) || 0;
            const ligneSousTotal = input.closest('.produit-ligne').querySelector('.sous-total-ligne');
            ligneSousTotal.textContent = (prix * quantite).toFixed(2) + ' €';
            calculerTotal();

            // Mettre à jour le panier en session
            syncPanier(input.dataset.reference, quantite);
        });
    });

    function calculerTotal() {
        let totalPrix = 0, totalQuantite = 0;
        inputs.forEach(input => {
            const prix = parseFloat(input.dataset.prix) || 0;
            const quantite = parseInt(input.value) || 0;
            totalPrix += prix * quantite;
            totalQuantite += quantite;
        });
        document.getElementById('total-commande').textContent = totalPrix.toFixed(2) + ' €';
        document.getElementById('total-quantite').textContent = totalQuantite;
    }

    // Calcul initial pour les produits pré-remplis depuis le panier
    inputs.forEach(input => {
        const prix = parseFloat(input.dataset.prix) || 0;
        const quantite = parseInt(input.value) || 0;
        if (quantite > 0) {
            const ligneSousTotal = input.closest('.produit-ligne').querySelector('.sous-total-ligne');
            ligneSousTotal.textContent = (prix * quantite).toFixed(2) + ' €';
        }
    });
    calculerTotal();

    // Vider le panier
    document.getElementById('vider-panier-btn').addEventListener('click', () => {
        fetch('/commandes/panier/vider/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                // Remettre toutes les quantités à 0
                inputs.forEach(input => {
                    input.value = 0;
                    input.closest('.produit-ligne').querySelector('.sous-total-ligne').textContent = '0.00 €';
                });
                calculerTotal();
                // Supprimer le badge
                const badge = document.getElementById('panier-badge');
                if (badge) badge.remove();
            }
        });
    });
});
