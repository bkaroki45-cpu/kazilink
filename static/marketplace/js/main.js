const root = document.documentElement;
root.dataset.theme = 'light';
localStorage.removeItem('kazisite-theme');

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

document.querySelectorAll('[data-back-button]').forEach((button) => {
    button.addEventListener('click', () => {
        if (window.history.length > 1) {
            window.history.back();
            return;
        }
        window.location.href = '/';
    });
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
                await navigator.share({ title: 'KaziSite job', url });
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

const mediaViewer = document.querySelector('[data-media-viewer]');
const mediaStage = document.querySelector('[data-media-stage]');
const mediaDownload = document.querySelector('[data-media-download]');
const closeMediaViewer = () => {
    if (!mediaViewer || !mediaStage) return;
    mediaViewer.hidden = true;
    mediaViewer.classList.remove('zoomed');
    mediaStage.innerHTML = '';
};

document.addEventListener('click', (event) => {
    const trigger = event.target.closest('[data-lightbox-src]');
    if (!trigger || !mediaViewer || !mediaStage) return;
    event.preventDefault();
    const src = trigger.dataset.lightboxSrc;
    const type = trigger.dataset.lightboxType || (trigger.tagName === 'VIDEO' ? 'video' : 'image');
    if (!src) return;
    mediaStage.innerHTML = '';
    const node = type === 'video' ? document.createElement('video') : document.createElement('img');
    node.src = src;
    if (type === 'video') {
        node.controls = true;
        node.autoplay = true;
    } else {
        node.alt = trigger.getAttribute('alt') || 'Preview';
    }
    mediaStage.appendChild(node);
    if (mediaDownload) mediaDownload.href = src;
    mediaViewer.hidden = false;
});

document.querySelector('[data-media-close]')?.addEventListener('click', closeMediaViewer);
document.querySelector('[data-media-zoom]')?.addEventListener('click', () => {
    mediaViewer?.classList.toggle('zoomed');
});
mediaViewer?.addEventListener('click', (event) => {
    if (event.target === mediaViewer) closeMediaViewer();
});
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMediaViewer();
});

function updateChatBadge(count) {
    const unreadCount = Number(count) || 0;
    document.querySelectorAll('[data-chat-badge]').forEach((badge) => {
        badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        badge.hidden = unreadCount <= 0;
    });
}

async function pollNotificationStatus() {
    try {
        const response = await fetch('/api/notifications/status/');
        if (!response.ok) return;
        const data = await response.json();
        updateChatBadge(data.unread_chats ?? data.unread_chat_threads ?? 0);

        const latest = data.latest;
        if (!('Notification' in window) || !latest || Notification.permission !== 'granted') return;
        const storageKey = 'kazisite-last-browser-note';
        if (localStorage.getItem(storageKey) === String(latest.id)) return;
        localStorage.setItem(storageKey, String(latest.id));
        const note = new Notification(latest.title, {
            body: latest.body || '',
            tag: `kazisite-${latest.id}`,
        });
        note.onclick = () => {
            window.focus();
            if (latest.url) {
                window.location.href = latest.url.startsWith('/chat/') ? '/inbox/' : latest.url;
            }
        };
    } catch (error) {
        /* Notifications are progressive enhancement. */
    }
}

function urlBase64ToUint8Array(value) {
    const padding = '='.repeat((4 - value.length % 4) % 4);
    const base64 = (value + padding).replace(/-/g, '+').replace(/_/g, '/');
    const raw = window.atob(base64);
    return Uint8Array.from([...raw].map((char) => char.charCodeAt(0)));
}

async function enablePushNotifications() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) return;
    if (Notification.permission === 'denied') return;

    const permission = Notification.permission === 'granted'
        ? 'granted'
        : await Notification.requestPermission();
    if (permission !== 'granted') return;

    const registration = await navigator.serviceWorker.register('/static/marketplace/js/sw.js?v=chat-open-guard-1');
    const configResponse = await fetch('/api/push/config/');
    if (!configResponse.ok) return;
    const config = await configResponse.json();
    if (!config.public_key) return;

    let subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
        subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(config.public_key),
        });
    }

    await fetch('/api/push/subscribe/', {
        method: 'POST',
        body: JSON.stringify(subscription),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || '',
        },
    });
}

setInterval(pollNotificationStatus, 15000);
pollNotificationStatus();

if ('Notification' in window) {
    const askOnce = () => {
        enablePushNotifications().catch(() => {});
        window.removeEventListener('click', askOnce);
        window.removeEventListener('touchstart', askOnce);
    };
    window.addEventListener('click', askOnce, { once: true });
    window.addEventListener('touchstart', askOnce, { once: true });
}
