/**
 * =============================================================================
 * COMMANDER.JS - Page de passage de commande
 * =============================================================================
 *
 * Ce module JavaScript gère les interactions de la page de commande
 * où l'utilisateur sélectionne ses produits et leurs quantités.
 *
 * Fonctionnalités principales :
 *   - Calcul automatique de la date de départ des camions (J-2)
 *   - Recherche et filtrage de produits en temps réel
 *   - Calcul des sous-totaux par ligne et total général
 *   - Synchronisation du panier en session (AJAX avec debounce)
 *   - Vidage complet du panier
 *
 * Architecture :
 *   - Utilise le debounce (400ms) pour limiter les requêtes au serveur
 *   - Synchronise automatiquement les quantités avec la session
 *   - Calcul des totaux côté client pour une expérience fluide
 *
 * Dépendances :
 *   - Bootstrap 5 (pour le style)
 *   - Token CSRF Django
 *
 * Projet : Extranet Giffaud Groupe
 * =============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {

    // =========================================================================
    // CALCUL AUTOMATIQUE DE LA DATE DE DÉPART
    // =========================================================================
    // La date de départ des camions est calculée comme étant 2 jours
    // avant la date de livraison souhaitée (placé en premier pour
    // s'assurer qu'il s'exécute même si le reste échoue)
    const dateLivraison = document.getElementById('date-livraison');
    const dateDepartCamions = document.getElementById('date-depart-camions');

    /**
     * Calcule et affiche la date de départ des camions.
     * Formule : Date départ = Date livraison - 2 jours
     */
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

    // =========================================================================
    // RECHERCHE DE PRODUITS EN TEMPS RÉEL
    // =========================================================================
    const rechercheInput = document.getElementById('recherche-produit');
    const effacerBtn = document.getElementById('effacer-recherche');
    const lignesProduits = document.querySelectorAll('.produit-ligne');

    // Sortir si pas d'éléments de recherche sur la page
    if (!rechercheInput) return;

    // Empêcher Entrée de soumettre le formulaire principal
    rechercheInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') e.preventDefault();
    });

    /**
     * Filtre les lignes de produits selon le texte de recherche.
     * Utilise !important pour surcharger les styles de liste_limite.js
     */
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

    // Bouton pour effacer la recherche
    effacerBtn.addEventListener('click', () => {
        rechercheInput.value = '';
        filtrerProduits();
        rechercheInput.focus();
    });

    // =========================================================================
    // TOKEN CSRF POUR LES REQUÊTES AJAX
    // =========================================================================
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // =========================================================================
    // SYNCHRONISATION AVEC LE PANIER EN SESSION
    // =========================================================================
    // Timers de debounce par référence produit pour éviter trop de requêtes
    const syncTimers = {};

    /**
     * Synchronise une quantité avec le panier en session.
     * Utilise un debounce de 400ms par référence produit.
     *
     * @param {string} reference - Référence du produit
     * @param {number} quantite - Nouvelle quantité
     */
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

    // =========================================================================
    // CALCUL DES TOTAUX
    // =========================================================================
    const inputs = document.querySelectorAll('.quantite-commande-input');

    // Écouteur sur chaque champ de quantité
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            const prix = parseFloat(input.dataset.prix) || 0;
            const quantite = parseInt(input.value) || 0;

            // Mise à jour du sous-total de la ligne
            const ligneSousTotal = input.closest('.produit-ligne').querySelector('.sous-total-ligne');
            ligneSousTotal.textContent = (prix * quantite).toFixed(2) + ' €';

            // Recalcul du total général
            calculerTotal();

            // Mettre à jour le panier en session
            syncPanier(input.dataset.reference, quantite);
        });
    });

    /**
     * Calcule et affiche le total général de la commande.
     * Somme tous les prix × quantités de la page.
     */
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

    // =========================================================================
    // INITIALISATION DES SOUS-TOTAUX
    // =========================================================================
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

    // =========================================================================
    // VIDAGE DU PANIER
    // =========================================================================
    // Bouton pour remettre toutes les quantités à zéro
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

    // =========================================================================
    // AJUSTEMENT DE LA HAUTEUR DU TABLEAU DES PRODUITS
    // =========================================================================
    /**
     * Ajuste la hauteur du tableau des produits pour correspondre
     * à la hauteur de la colonne droite sur grand écran.
     */
    function ajusterHauteurProduits() {
        const tableContainer = document.getElementById('produits-table-container');
        if (!tableContainer) return;

        if (window.innerWidth >= 992) {
            const colonneDroite = document.getElementById('colonne-droite');
            if (colonneDroite) {
                const hauteurDroite = colonneDroite.offsetHeight;
                const titreHauteur = tableContainer.previousElementSibling
                    ? tableContainer.previousElementSibling.offsetHeight + 16
                    : 60;
                tableContainer.style.maxHeight = (hauteurDroite - titreHauteur) + 'px';
            }
        } else {
            tableContainer.style.maxHeight = '400px';
        }
    }

    // Exécuter au chargement et au redimensionnement
    window.addEventListener('load', ajusterHauteurProduits);
    window.addEventListener('resize', ajusterHauteurProduits);

    // =========================================================================
    // OUVERTURE DU SÉLECTEUR DE DATE AU CLIC
    // =========================================================================
    if (dateLivraison) {
        dateLivraison.addEventListener('click', function() {
            this.showPicker();
        });
    }

    // =========================================================================
    // GESTION DES BOUTONS +/-
    // =========================================================================
    document.querySelectorAll('.quantite-groupe').forEach(groupe => {
        const btnMoins = groupe.querySelector('.btn-moins');
        const btnPlus = groupe.querySelector('.btn-plus');
        const input = groupe.querySelector('.quantite-commande-input');

        if (btnMoins) {
            btnMoins.addEventListener('click', () => {
                const val = parseInt(input.value) || 0;
                if (val > 0) {
                    input.value = val - 1;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
        }

        if (btnPlus) {
            btnPlus.addEventListener('click', () => {
                const val = parseInt(input.value) || 0;
                input.value = val + 1;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            });
        }
    });
});
