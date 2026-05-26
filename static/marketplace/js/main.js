const navToggle = document.querySelector('[data-nav-toggle]');
const navLinks = document.querySelector('[data-nav-links]');
const drawerBackdrop = document.querySelector('[data-drawer-backdrop]');

if (navToggle && navLinks) {
    const setDrawer = (open) => {
        navLinks.classList.toggle('open', open);
        drawerBackdrop?.classList.toggle('open', open);
        navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    };

    navToggle.addEventListener('click', () => setDrawer(!navLinks.classList.contains('open')));
    drawerBackdrop?.addEventListener('click', () => setDrawer(false));
    navLinks.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', () => setDrawer(false));
    });
}

document.querySelectorAll('[data-share]').forEach((button) => {
    button.addEventListener('click', async () => {
        const url = button.dataset.share;
        if (navigator.share) {
            await navigator.share({ title: 'KaziLink job', url });
        } else {
            await navigator.clipboard.writeText(url);
            button.textContent = 'Copied';
        }
    });
});
