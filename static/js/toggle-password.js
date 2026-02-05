/**
 * =============================================================================
 * TOGGLE-PASSWORD.JS - Affichage/masquage des mots de passe
 * =============================================================================
 *
 * Ce module JavaScript permet aux utilisateurs de basculer la visibilité
 * des champs de mot de passe dans les formulaires de connexion et
 * de modification de mot de passe.
 *
 * Fonctionnalités :
 *   - Basculement entre type "password" et "text"
 *   - Changement de l'icône (œil ouvert → œil barré)
 *   - Deux modes d'utilisation : auto-init et manuel
 *
 * Mode auto-init (recommandé) :
 *   <input type="password" id="mon-mdp">
 *   <button type="button" class="toggle-password" data-target="mon-mdp">
 *     <i class="bi bi-eye"></i>
 *   </button>
 *
 * Mode manuel (pour cas particuliers) :
 *   <input type="password" id="mon-mdp">
 *   <button type="button" onclick="togglePassword('mon-mdp', this)">
 *     <i class="bi bi-eye"></i>
 *   </button>
 *
 * Dépendances :
 *   - Bootstrap Icons (bi-eye et bi-eye-slash)
 *
 * Projet : Extranet Giffaud Groupe
 * =============================================================================
 */


/**
 * Initialise automatiquement les boutons de toggle password.
 *
 * Recherche tous les boutons avec la classe .toggle-password et leur
 * attache un événement click. Le champ cible est identifié par
 * l'attribut data-target du bouton.
 *
 * Appelée automatiquement au chargement du DOM.
 */
function initTogglePassword() {
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            // Récupération de l'input cible via data-target
            const input = document.getElementById(this.dataset.target);
            const icon = this.querySelector('i');

            // Basculement du type et de l'icône
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    });
}


/**
 * Bascule la visibilité d'un champ mot de passe (mode manuel).
 *
 * Cette fonction est utilisée dans les templates où l'on préfère
 * passer les paramètres directement via onclick plutôt que
 * d'utiliser les data-attributes.
 *
 * @param {string} inputId - L'ID du champ input à basculer
 * @param {HTMLElement} button - Le bouton cliqué (pour accéder à l'icône)
 *
 * @example
 * <button onclick="togglePassword('password', this)">
 *   <i class="bi bi-eye"></i>
 * </button>
 */
function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    const icon = button.querySelector('i');

    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
    }
}


// Auto-init au chargement du DOM
document.addEventListener('DOMContentLoaded', initTogglePassword);
