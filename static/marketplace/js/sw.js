self.addEventListener('push', (event) => {
    let payload = {};
    try {
        payload = event.data ? event.data.json() : {};
    } catch (error) {
        payload = { title: 'KaziSite', body: event.data ? event.data.text() : '' };
    }

    const title = payload.title || 'KaziSite';
    const options = {
        body: payload.body || '',
        data: { url: payload.url || '/notifications/' },
        tag: payload.url || title,
        icon: '/static/marketplace/images/home.png',
        badge: '/static/marketplace/images/home.png',
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const payloadUrl = event.notification.data?.url || '/notifications/';
    const url = payloadUrl.startsWith('/chat/') ? '/inbox/' : payloadUrl;
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            const existing = clientList.find((client) => client.url.includes(url));
            if (existing) return existing.focus();
            return clients.openWindow(url);
        })
    );
});
