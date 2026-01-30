/**
 * Ouvre automatiquement les groupes d'accordéon qui ont des filtres cochés
 */
function initAccordionFiltres() {
    document.querySelectorAll('#accordionFiltres .accordion-item').forEach(function(item) {
        if (item.querySelector('input[type="checkbox"]:checked')) {
            var collapse = item.querySelector('.accordion-collapse');
            collapse.classList.add('show');
            var btn = item.querySelector('.accordion-button');
            btn.classList.remove('collapsed');
            btn.setAttribute('aria-expanded', 'true');
        }
    });
}

// Auto-init au chargement du DOM
document.addEventListener('DOMContentLoaded', initAccordionFiltres);
