// Limite le nombre d'éléments affichés selon la taille de l'écran
// Petit écran (<768px) : 20 éléments
// Moyen écran (768-1199px) : 60 éléments
// Grand écran (>=1200px) : tous

document.addEventListener('DOMContentLoaded', () => {
    const conteneurs = document.querySelectorAll('[data-liste-limitee]');
    if (!conteneurs.length) return;

    function getLimite() {
        const w = window.innerWidth;
        if (w < 768) return 20;
        if (w < 1200) return 60;
        return Infinity;
    }

    // Trouver l'élément parent où insérer le bouton "Voir plus"
    // Pour un <tbody>, on remonte au-dessus du <table> (ou .table-responsive)
    function getInsertParent(conteneur) {
        if (conteneur.tagName === 'TBODY') {
            const table = conteneur.closest('table');
            const wrapper = table.closest('.table-responsive');
            return wrapper || table;
        }
        return conteneur;
    }

    function appliquerLimite() {
        const limite = getLimite();

        conteneurs.forEach(conteneur => {
            const items = Array.from(conteneur.children).filter(
                el => !el.classList.contains('voir-plus-wrapper')
            );
            let nbCaches = 0;

            for (let i = 0; i < items.length; i++) {
                if (i < limite) {
                    items[i].style.removeProperty('display');
                } else {
                    items[i].style.setProperty('display', 'none', 'important');
                    nbCaches++;
                }
            }

            // Gérer le bouton "Voir plus"
            const insertParent = getInsertParent(conteneur);
            let btn = insertParent.parentElement.querySelector('.voir-plus-wrapper');

            if (nbCaches > 0) {
                if (!btn) {
                    btn = document.createElement('div');
                    btn.className = 'voir-plus-wrapper text-center mt-3 mb-4';
                    btn.innerHTML = '<button class="btn btn-outline-primary btn-voir-plus"><i class="bi bi-chevron-down"></i> Voir plus (' + nbCaches + ' restants)</button>';
                    insertParent.parentElement.insertBefore(btn, insertParent.nextSibling);

                    btn.querySelector('.btn-voir-plus').addEventListener('click', () => {
                        for (let i = 0; i < items.length; i++) {
                            items[i].style.removeProperty('display');
                        }
                        btn.remove();
                    });
                } else {
                    btn.querySelector('.btn-voir-plus').innerHTML = '<i class="bi bi-chevron-down"></i> Voir plus (' + nbCaches + ' restants)';
                }
            } else if (btn) {
                btn.remove();
            }
        });
    }

    appliquerLimite();
    window.addEventListener('resize', appliquerLimite);
});
