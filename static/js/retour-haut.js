/**
 * Script pour le bouton "Retour en haut"
 * Affiche un bouton flottant après 300px de défilement
 * Au clic, remonte en haut de la page avec animation fluide
 */
(function() {
    const btn = document.getElementById('btn-retour-haut');
    if (!btn) return;

    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    });

    btn.addEventListener('click', function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
})();
