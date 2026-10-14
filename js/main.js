import {installGallery} from './gallery.js?v=2.2.0';
// One application shell and router. Game modules own only their reference data and rules.
const container = document.getElementById('view-container');
const sidebar = document.getElementById('sidebar');
const menuToggle = document.getElementById('menu-toggle');
const backdrop = document.getElementById('menu-backdrop');
const mobile = matchMedia('(max-width: 768px)');
function setMenu(open) {
    sidebar.classList.toggle('collapsed', !open);
    menuToggle.setAttribute('aria-expanded', String(open));
    sidebar.inert = mobile.matches && !open;
    sidebar.setAttribute('aria-hidden', String(mobile.matches && !open));
    backdrop.hidden = !mobile.matches || !open;
}
mobile.addEventListener('change', () => setMenu(false));
setMenu(false);
installGallery(container);
const nav = sidebar.querySelector('nav ul');
const search = document.getElementById('main-search');
const ds2Nav = nav.innerHTML;
const navIcons = Object.fromEntries([...nav.querySelectorAll('[data-tab]')].map(li => [li.dataset.tab, li.querySelector('img')?.getAttribute('src')]));
const modules = new Map();
let activeGame = '', revision = 0;

function route() {
    const p = new URLSearchParams(location.hash.slice(1));
    // Existing DS2 bookmarks remain valid; a fresh launch opens the game menu.
    return {game: p.get('game') || (p.get('view') && p.get('view') !== 'games' ? 'ds2' : ''),
        view: p.get('view') || 'home', id: p.get('id') || undefined,
        ids: p.get('ids')?.split(',')};
}
async function loadGame(game) {
    if (!modules.has(game)) modules.set(game, (async () => {
        if (game === 'ds1') {
            const module = await import('./ds1.js?v=2.1.0');
            await module.load();
            return module;
        }
        const {CodexApp} = await import('./app.js?v=2.1.0');
        const app = new CodexApp();
        await app.loading;
        window.app = app;
        return app;
    })());
    try { return await modules.get(game); }
    catch (error) { modules.delete(game); throw error; }
}
function menu() {
    document.title = 'Souls Companion · Dark Souls Guide';
    container.innerHTML = `<div class="game-hub"><p class="hub-eyebrow">SOULS COMPANION</p>
        <h1>Choose your world</h1><p>Explore the guides, plan your equipment, and build your character.</p>
        <div class="game-cards">
        <a class="game-card" href="#game=ds1&view=home"><span class="roman">I</span><h2>Dark Souls I</h2><p>Lordran · Remastered · Artorias of the Abyss</p><strong>Enter Lordran →</strong></a>
        <a class="game-card" href="#game=ds2&view=home"><span class="roman">II</span><h2>Dark Souls II</h2><p>Drangleic · Scholar of the First Sin · The Lost Crowns</p><strong>Enter Drangleic →</strong></a>
        <div class="game-card planned"><span class="roman">III</span><h2>Dark Souls III</h2><p>Lothric</p><strong>Coming later</strong></div></div>
        <p class="hub-note">Your builds, favorites, and journals stay saved on this device for each game.</p></div>`;
}
async function show() {
    if (mobile.matches) setMenu(false);
    const token = ++revision, r = route();
    if (r.game && !['ds1','ds2'].includes(r.game)) {
        location.hash = 'view=games'; return;
    }
    if (r.game && !new URLSearchParams(location.hash.slice(1)).has('game')) {
        const p = new URLSearchParams(location.hash.slice(1)); p.set('game', r.game);
        history.replaceState(null, '', '#' + p);
    }
    activeGame = r.game;
    document.body.className = 'ds-theme ' + (r.game ? 'game-' + r.game : 'game-menu');
    document.getElementById('game-title').textContent = r.game === 'ds1' ? 'DS I' : r.game === 'ds2' ? 'DS II' : 'SOULS';
    document.getElementById('game-label').textContent = r.game === 'ds1' ? 'Dark Souls I' : r.game === 'ds2' ? 'Dark Souls II' : '';
    search.value = ''; search.disabled = !r.game;
    search.placeholder = r.game ? `Search Dark Souls ${r.game === 'ds1' ? 'I' : 'II'}…` : 'Choose a game to search';
    document.getElementById('modal-container').innerHTML = '';
    if (!r.game) { nav.innerHTML = ''; menu(); return; }
    nav.innerHTML = ''; container.innerHTML = '<p>Loading the local archive…</p>';
    try {
        const module = await loadGame(r.game);
        if (token !== revision) return;
        if (r.game === 'ds1') {
            nav.innerHTML = Object.entries(module.labels).map(([key,label]) => `<li data-tab="${key}" title="${label}"><img class="nav-icon" alt="" src="${navIcons[key] || 'assets/ui/stat/stat-souls.webp'}"><span class="nav-text">${label}</span></li>`).join('');
            module.show();
        } else {
            nav.innerHTML = ds2Nav;
            module.renderView(r.view, {id:r.id, ...(r.ids ? {ids:r.ids} : {})});
            document.title = 'Dark Souls II · Companion Guide';
        }
        nav.querySelectorAll('li').forEach(li => {
            li.tabIndex = 0; li.setAttribute('role', 'link'); li.title = li.textContent.trim();
            if (r.game === 'ds1') li.classList.toggle('active', li.dataset.tab === r.view);
        });
        document.querySelector('.content-area').scrollTop = 0;
    } catch (error) {
        if (token !== revision) return;
        container.replaceChildren(Object.assign(document.createElement('p'), {textContent: `Could not load the archive: ${error.message}`}));
    }
}
function openTab(li) { if (li && activeGame) {if (mobile.matches) setMenu(false);location.hash = new URLSearchParams({game:activeGame, view:li.dataset.tab});} }
nav.addEventListener('click', e => openTab(e.target.closest('[data-tab]')));
nav.addEventListener('keydown', e => {if (e.key === 'Enter' || e.key === ' ') {e.preventDefault();openTab(e.target.closest('[data-tab]'));}});
menuToggle.addEventListener('click', () => setMenu(sidebar.classList.contains('collapsed')));
backdrop.addEventListener('click', () => setMenu(false));
document.addEventListener('keydown', event => {if (event.key === 'Escape' && !sidebar.classList.contains('collapsed')) {setMenu(false);menuToggle.focus();}});
search.addEventListener('focus', () => {if (mobile.matches) setMenu(false);});
search.addEventListener('pointerdown', () => {if (mobile.matches) setMenu(false);});
search.addEventListener('input', async () => {
    const game = activeGame, value = search.value, token = revision;
    if (!game) return;
    const module = await loadGame(game);
    if (token !== revision || value !== search.value) return;
    if (game === 'ds1') module.handleSearch(value);
    else if (value) module.handleSearch(value);
    else module.renderView(module.currentView, module.currentParams);
});
container.addEventListener('click', e => {
    const link = e.target.closest('a[data-view]');
    if (!link || activeGame !== 'ds2' || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    e.preventDefault(); location.hash = new URLSearchParams({game:'ds2',view:link.dataset.view,id:link.dataset.id});
});
window.addEventListener('hashchange', show);
show();
