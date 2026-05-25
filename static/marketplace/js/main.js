const navToggle = document.querySelector('[data-nav-toggle]');
const navLinks = document.querySelector('[data-nav-links]');

if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
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
