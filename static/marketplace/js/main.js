const root = document.documentElement;
const storedTheme = localStorage.getItem('kazilink-theme');
const systemDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches;
root.dataset.theme = storedTheme || (systemDark ? 'dark' : 'light');

const setTheme = (theme) => {
    root.dataset.theme = theme;
    localStorage.setItem('kazilink-theme', theme);
    document.querySelectorAll('[data-theme-icon]').forEach((icon) => {
        icon.textContent = theme === 'dark' ? '☾' : '☀';
    });
};
setTheme(root.dataset.theme);

document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
    button.addEventListener('click', () => {
        setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
    });
});

const navToggle = document.querySelector('[data-nav-toggle]');
const navLinks = document.querySelector('[data-nav-links]');
const drawerBackdrop = document.querySelector('[data-drawer-backdrop]');

if (navToggle && navLinks) {
    const setDrawer = (open) => {
        navLinks.classList.toggle('open', open);
        drawerBackdrop?.classList.toggle('open', open);
        navToggle.classList.toggle('open', open);
        navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        document.body.style.overflow = open ? 'hidden' : '';
        document.body.classList.toggle('drawer-open', open);
    };

    navToggle.addEventListener('click', () => setDrawer(!navLinks.classList.contains('open')));
    drawerBackdrop?.addEventListener('click', () => setDrawer(false));
    navLinks.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setDrawer(false)));
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') setDrawer(false);
    });
}

const topbar = document.querySelector('.topbar');
if (topbar) {
    const updateTopbar = () => topbar.classList.toggle('is-shrunk', window.scrollY > 16);
    updateTopbar();
    window.addEventListener('scroll', updateTopbar, { passive: true });
}

document.querySelectorAll('[data-profile-menu]').forEach((menu) => {
    const trigger = menu.querySelector('[data-profile-toggle]');
    trigger?.addEventListener('click', () => {
        const open = !menu.classList.contains('open');
        document.querySelectorAll('[data-profile-menu].open').forEach((item) => item.classList.remove('open'));
        menu.classList.toggle('open', open);
        trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', (event) => {
        if (!menu.contains(event.target)) menu.classList.remove('open');
    });
});

const currentPath = window.location.pathname;
document.querySelectorAll('.nav-links a, .bottom-nav a').forEach((link) => {
    if (link.href && new URL(link.href).pathname === currentPath) link.classList.add('active');
});

document.querySelectorAll('.toast').forEach((toast) => {
    setTimeout(() => {
        toast.style.transition = 'opacity .4s ease, transform .4s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        setTimeout(() => toast.remove(), 420);
    }, 4200);
});

document.querySelectorAll('[data-password-toggle]').forEach((toggle) => {
    toggle.addEventListener('click', () => {
        const input = toggle.parentElement.querySelector('input');
        if (!input) return;
        const show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        toggle.textContent = show ? 'Hide' : 'Show';
    });
});

document.querySelectorAll('.floating-field input, .floating-field textarea').forEach((input) => {
    if (!input.getAttribute('placeholder')) input.setAttribute('placeholder', ' ');
});

document.querySelectorAll('[data-share]').forEach((button) => {
    button.addEventListener('click', async () => {
        const url = button.dataset.share;
        const count = button.querySelector('[data-count]');
        if (count) count.textContent = Number(count.textContent || 0) + 1;
        button.classList.add('is-shared');
        try {
            if (navigator.share) {
                await navigator.share({ title: 'KaziLink job', url });
            } else {
                await navigator.clipboard.writeText(url);
                button.dataset.copied = 'true';
                setTimeout(() => delete button.dataset.copied, 1500);
            }
        } catch (error) {
            button.classList.remove('is-shared');
        }
    });
});

document.querySelectorAll('[data-ajax-action]').forEach((form) => {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const button = form.querySelector('button');
        button?.classList.add('is-loading');
        const response = await fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        button?.classList.remove('is-loading');
        if (!response.ok) {
            form.submit();
            return;
        }
        const data = await response.json();
        const label = button?.querySelector('[data-label]');
        const count = button?.querySelector('[data-count]');
        form.classList.toggle('is-active', Boolean(data.active));
        if (label) label.textContent = data.label;
        if (count && data.count !== undefined) count.textContent = data.count;
        button?.classList.add('pop');
        setTimeout(() => button?.classList.remove('pop'), 240);
    });
});
