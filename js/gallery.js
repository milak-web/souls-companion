// Shared catalog density, independent of a game's filters and calculations.
export function installGallery(container) {
    const sizes = ['large', 'compact', 'small'];
    let size = 'compact';
    const mobile = matchMedia('(max-width:768px)');
    let filtersOpen = false;
    try { const saved = localStorage.getItem('souls_gallery_size'); if (sizes.includes(saved)) size = saved; } catch {}
    function update() {
        container.querySelectorAll('[data-gallery-grid]').forEach(grid => grid.dataset.gallerySize = size);
        container.querySelectorAll('[data-gallery-size]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.gallerySize === size)));
    }
    function decorate() {
        container.querySelectorAll('.catalog-controls, .toolbar').forEach(controls => {
            if (controls.closest('.mobile-filters')) return;
            const details = document.createElement('details');
            details.className = 'mobile-filters';
            details.open = !mobile.matches || filtersOpen;
            const summary = document.createElement('summary');
            summary.textContent = 'Filters & sorting';
            details.append(summary);
            controls.before(details);
            details.append(controls);
            details.addEventListener('toggle', () => {if (mobile.matches) filtersOpen = details.open;});
        });
        container.querySelectorAll('.card-grid, .grid:not(.home-links)').forEach(grid => {
            if (!grid.children.length || grid.hasAttribute('data-gallery-grid')) return;
            grid.dataset.galleryGrid = '';
            const toolbar = document.createElement('div');
            toolbar.className = 'gallery-controls';
            toolbar.setAttribute('role', 'group');
            toolbar.setAttribute('aria-label', 'Gallery card size');
            toolbar.innerHTML = `<span>Card size</span>${sizes.map(value => `<button type="button" data-gallery-size="${value}" aria-pressed="${value === size}">${value[0].toUpperCase() + value.slice(1)}</button>`).join('')}`;
            grid.before(toolbar);
        });
        update();
    }
    container.addEventListener('click', event => {
        const button = event.target.closest('[data-gallery-size]');
        if (!button) return;
        size = button.dataset.gallerySize;
        try { localStorage.setItem('souls_gallery_size', size); } catch {}
        update();
    });
    new MutationObserver(decorate).observe(container, {childList:true, subtree:true});
    mobile.addEventListener('change', () => container.querySelectorAll('.mobile-filters').forEach(details => details.open = !mobile.matches || filtersOpen));
    decorate();
}
