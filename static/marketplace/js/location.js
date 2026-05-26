function getCookie(name) {
    return document.cookie.split('; ').find((row) => row.startsWith(`${name}=`))?.split('=')[1];
}

function fieldScope(element) {
    return element?.closest('form') || document;
}

function setLocationInputs(lat, lng, scope = document) {
    const latInput = scope.querySelector('[name="latitude"], [name="place_lat"]');
    const lngInput = scope.querySelector('[name="longitude"], [name="place_lng"]');
    if (lat === '' || lng === '') {
        if (latInput) latInput.value = '';
        if (lngInput) lngInput.value = '';
        return;
    }
    if (latInput) latInput.value = Number(lat).toFixed(6);
    if (lngInput) lngInput.value = Number(lng).toFixed(6);
}

function renderLocationPreview(lat, lng, label = 'Selected location') {
    const latNumber = Number(lat);
    const lngNumber = Number(lng);
    const preview = document.querySelector('#map-preview');
    if (!preview || !Number.isFinite(latNumber) || !Number.isFinite(lngNumber)) return;

    preview.innerHTML = `<iframe title="OpenStreetMap preview" width="100%" height="220" style="border:0;border-radius:8px" src="https://www.openstreetmap.org/export/embed.html?bbox=${lngNumber - 0.02}%2C${latNumber - 0.02}%2C${lngNumber + 0.02}%2C${latNumber + 0.02}&layer=mapnik&marker=${latNumber}%2C${lngNumber}"></iframe><span class="preview-label">${label}</span>`;
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
            console.log('User latitude:', Number(lat));
            console.log('User longitude:', Number(lng));
            setLocationInputs(lat, lng);
            renderLocationPreview(lat, lng, 'GPS location detected');
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
            timeout: 10000,
            maximumAge: 0,
        });
    });
});

function initLocationAutocomplete() {
    document.querySelectorAll('[data-location-search]').forEach((input) => {
        const scope = fieldScope(input);
        const list = input.parentElement?.querySelector('[data-location-suggestions]') || scope.querySelector('[data-location-suggestions]');
        if (!list) return;

        let timer = null;
        let activeController = null;

        function clearSuggestions() {
            list.innerHTML = '';
            list.hidden = true;
        }

        function choosePlace(place) {
            input.value = place.name;
            const placeName = scope.querySelector('[data-place-name]');
            if (placeName) placeName.value = place.name;
            setLocationInputs(place.lat, place.lng, scope);
            renderLocationPreview(place.lat, place.lng, place.name);
            clearSuggestions();
        }

        function renderSuggestions(results) {
            list.innerHTML = '';
            list.hidden = !results.length;
            results.forEach((place) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.innerHTML = `<strong>${place.name}</strong><span>${place.type || 'place'}</span>`;
                button.addEventListener('click', () => choosePlace(place));
                list.appendChild(button);
            });
        }

        async function searchLocations(query) {
            if (query.length < 2) {
                clearSuggestions();
                return;
            }

            activeController?.abort();
            activeController = new AbortController();
            list.hidden = false;
            list.innerHTML = '<div class="location-suggestion-empty">Searching exact places...</div>';

            try {
                const response = await fetch(`/api/geocode/?q=${encodeURIComponent(query)}`, {
                    signal: activeController.signal,
                });
                if (!response.ok) throw new Error(`Geocoder failed with ${response.status}`);
                const data = await response.json();
                renderSuggestions(data.results || []);
                if (!data.results?.length) {
                    list.hidden = false;
                    list.innerHTML = '<div class="location-suggestion-empty">No match found. Use the map picker if available.</div>';
                }
            } catch (error) {
                if (error.name === 'AbortError') return;
                list.hidden = false;
                list.innerHTML = '<div class="location-suggestion-empty">Search failed. Use the map picker if available.</div>';
            }
        }

        input.addEventListener('input', () => {
            setLocationInputs('', '', scope);
            const placeName = scope.querySelector('[data-place-name]');
            if (placeName) placeName.value = '';
            window.clearTimeout(timer);
            timer = window.setTimeout(() => searchLocations(input.value.trim()), 350);
        });

        input.addEventListener('blur', () => {
            window.setTimeout(clearSuggestions, 180);
        });
    });
}

function initMapPicker() {
    const toggle = document.querySelector('[data-map-picker-toggle]');
    const picker = document.querySelector('[data-map-picker]');
    const mapEl = document.querySelector('#post-location-map');
    if (!toggle || !picker || !mapEl || !window.maplibregl) return;

    let map = null;
    let marker = null;

    function ensureMap() {
        if (map) {
            map.resize();
            return;
        }

        map = new maplibregl.Map({
            container: mapEl,
            style: 'https://tiles.openfreemap.org/styles/liberty',
            center: [36.9476, -0.4201],
            zoom: 12,
            minZoom: 6,
            maxZoom: 21,
            maxBounds: [[33.5, -4.9], [42.1, 5.3]],
            attributionControl: false,
        });
        map.addControl(new maplibregl.NavigationControl(), 'top-right');
        map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

        map.on('click', (event) => {
            const { lat, lng } = event.lngLat;
            setLocationInputs(lat, lng, fieldScope(mapEl));
            renderLocationPreview(lat, lng, 'Map pin selected');
            if (marker) marker.remove();
            marker = new maplibregl.Marker({ color: '#00c46a' })
                .setLngLat([lng, lat])
                .addTo(map);
        });
    }

    toggle.addEventListener('click', () => {
        picker.hidden = !picker.hidden;
        toggle.textContent = picker.hidden ? 'Pick exact place on map' : 'Hide map picker';
        if (!picker.hidden) {
            window.setTimeout(ensureMap, 50);
        }
    });
}

initLocationAutocomplete();
initMapPicker();
