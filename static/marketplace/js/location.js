function getCookie(name) {
    return document.cookie.split('; ').find((row) => row.startsWith(`${name}=`))?.split('=')[1];
}

document.querySelectorAll('[data-detect-location]').forEach((button) => {
    button.addEventListener('click', () => {
        const originalText = button.textContent.trim();
        if (!navigator.geolocation) {
            button.textContent = 'GPS unavailable';
            return;
        }
        button.textContent = 'Detecting...';
        button.disabled = true;
        navigator.geolocation.getCurrentPosition((position) => {
            const lat = position.coords.latitude.toFixed(6);
            const lng = position.coords.longitude.toFixed(6);
            const latNumber = Number(lat);
            const lngNumber = Number(lng);
            const latInput = document.querySelector('[name="latitude"]');
            const lngInput = document.querySelector('[name="longitude"]');
            if (latInput) latInput.value = lat;
            if (lngInput) lngInput.value = lng;
            const preview = document.querySelector('#map-preview');
            if (preview) {
                preview.innerHTML = `<iframe title="OpenStreetMap preview" width="100%" height="220" style="border:0;border-radius:8px" src="https://www.openstreetmap.org/export/embed.html?bbox=${lngNumber - 0.02}%2C${latNumber - 0.02}%2C${lngNumber + 0.02}%2C${latNumber + 0.02}&layer=mapnik&marker=${lat}%2C${lng}"></iframe>`;
            }
            fetch('/api/location/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCookie('csrftoken') },
                body: new URLSearchParams({ latitude: lat, longitude: lng }),
            }).catch(() => {});
            button.textContent = 'Location detected';
            if (button.dataset.nearbyTarget === 'reload') {
                const url = new URL(window.location.href);
                url.searchParams.set('nearby', '1');
                window.location.href = url.toString();
            } else if (button.dataset.nearbyTarget === 'reload-current') {
                window.location.reload();
            } else {
                window.setTimeout(() => {
                    button.textContent = originalText || 'Use GPS';
                    button.disabled = false;
                }, 1800);
            }
        }, (error) => {
            button.textContent = 'Allow GPS access';
            button.disabled = false;
            button.title = error.message || 'Your browser blocked location access.';
        }, {
            enableHighAccuracy: true,
            timeout: 12000,
            maximumAge: 60000,
        });
    });
});
