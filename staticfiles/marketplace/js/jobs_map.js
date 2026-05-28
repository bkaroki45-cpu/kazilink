const KENYA_CENTER = [36.817223, -1.286389];
const KENYA_BOUNDS = [[33.5, -4.9], [42.1, 5.3]];
const OPENFREEMAP_STYLE = 'https://tiles.openfreemap.org/styles/liberty';
const PHOTON_URL = 'https://photon.komoot.io/api/';
const NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search';
const OSRM_ROUTE_URL = 'https://router.project-osrm.org/route/v1/driving';

function validPoint(lat, lng) {
    return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
}

function pointInKenya(lat, lng) {
    return validPoint(lat, lng) && lat >= -4.9 && lat <= 5.3 && lng >= 33.5 && lng <= 42.1;
}

function normalizePoint(lat, lng, requireKenya = false) {
    const latitude = Number(lat);
    const longitude = Number(lng);

    if (requireKenya && pointInKenya(latitude, longitude)) return [latitude, longitude];
    if (requireKenya && pointInKenya(longitude, latitude)) return [longitude, latitude];
    if (!requireKenya && validPoint(latitude, longitude)) return [latitude, longitude];
    if (!requireKenya && validPoint(longitude, latitude)) return [longitude, latitude];
    return null;
}

function liveGpsOptions() {
    return {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
    };
}

function getLiveUserPoint(onSuccess, onError) {
    if (!navigator.geolocation) {
        onError('Your browser does not support GPS location.');
        return;
    }

    navigator.geolocation.getCurrentPosition((position) => {
        const point = normalizePoint(position.coords.latitude, position.coords.longitude, true);
        if (!point) {
            onError('Your GPS returned a location outside Kenya or invalid coordinates.');
            return;
        }
        onSuccess(point);
    }, (error) => {
        console.warn('GPS permission or location error:', error.message);
        onError('Please enable location access so KaziLink can show where you are on the map.');
    }, liveGpsOptions());
}

function toLngLat(point) {
    return [point[1], point[0]];
}

function mapBoundsFromPoints(points) {
    return points.reduce((bounds, point) => bounds.extend(toLngLat(point)), new maplibregl.LngLatBounds(toLngLat(points[0]), toLngLat(points[0])));
}

function fitMap(map, points, fallback) {
    if (points.length > 1) {
        map.fitBounds(mapBoundsFromPoints(points), { padding: 90, maxZoom: 17, duration: 900 });
    } else if (points.length === 1) {
        map.flyTo({ center: toLngLat(points[0]), zoom: 17, duration: 900 });
    } else {
        map.flyTo({ center: toLngLat(fallback), zoom: 12, duration: 900 });
    }
}

function formatDistance(meters) {
    if (!Number.isFinite(meters)) return '';
    return meters >= 1000 ? `${(meters / 1000).toFixed(1)} km` : `${Math.round(meters)} m`;
}

function formatTime(seconds) {
    if (!Number.isFinite(seconds)) return '';
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const remainder = minutes % 60;
    return remainder ? `${hours} hr ${remainder} min` : `${hours} hr`;
}

function markerElement(className, label) {
    const wrap = document.createElement('div');
    wrap.className = 'map-pin-wrap';
    wrap.innerHTML = `<span class="map-pin ${className}"><span>${label}</span></span>`;
    return wrap;
}

function addDetailedBuildingLayer(map) {
    const sourceId = map.getSource('openmaptiles') ? 'openmaptiles' : Object.keys(map.getStyle().sources || {})[0];
    if (!sourceId || map.getLayer('kazilink-building-extrusions')) return;

    try {
        map.addLayer({
            id: 'kazilink-building-extrusions',
            type: 'fill-extrusion',
            source: sourceId,
            'source-layer': 'building',
            minzoom: 15,
            paint: {
                'fill-extrusion-color': '#d4c7b6',
                'fill-extrusion-height': ['to-number', ['coalesce', ['get', 'render_height'], ['get', 'height']], 8],
                'fill-extrusion-base': ['to-number', ['coalesce', ['get', 'render_min_height'], ['get', 'min_height']], 0],
                'fill-extrusion-opacity': 0.58,
            },
        }, findFirstLabelLayer(map));
    } catch (error) {
        console.info('Building extrusion layer is unavailable for this vector style.', error);
    }
}

function findFirstLabelLayer(map) {
    const layers = map.getStyle().layers || [];
    const label = layers.find((layer) => layer.type === 'symbol' && layer.layout && layer.layout['text-field']);
    return label ? label.id : undefined;
}

function createMap(container, center = KENYA_CENTER, zoom = 12) {
    const map = new maplibregl.Map({
        container,
        style: OPENFREEMAP_STYLE,
        center,
        zoom,
        minZoom: 6,
        maxZoom: 21,
        maxBounds: KENYA_BOUNDS,
        attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');
    map.addControl(new maplibregl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: false,
    }), 'top-right');
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');
    map.on('load', () => addDetailedBuildingLayer(map));
    return map;
}

function createRoutePanel(map) {
    let container;
    let userPoint = null;
    let jobPoint = null;

    const control = {
        onAdd() {
            container = document.createElement('div');
            container.className = 'map-route-panel';
            container.innerHTML = `
                <strong>Route</strong>
                <span data-route-status>Select a job to calculate the road route.</span>
                <button type="button" data-open-route disabled>Open route</button>
            `;
            container.querySelector('[data-open-route]').addEventListener('click', () => {
                if (!userPoint || !jobPoint) return;
                window.open(`https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=${userPoint[0]},${userPoint[1]};${jobPoint[0]},${jobPoint[1]}`, '_blank', 'noopener');
            });
            return container;
        },
        onRemove() {
            container?.remove();
        },
    };

    map.addControl(control, 'bottom-left');

    return {
        setRoute(nextUserPoint, nextJobPoint) {
            userPoint = nextUserPoint;
            jobPoint = nextJobPoint;
            if (!container) return;
            container.querySelector('[data-route-status]').textContent = 'Calculating road route...';
            container.querySelector('[data-open-route]').disabled = false;
        },
        setSummary(distance, time) {
            if (!container) return;
            container.querySelector('[data-route-status]').textContent = `${formatDistance(distance)} / ${formatTime(time)}`;
        },
        setMessage(message) {
            if (!container) return;
            container.querySelector('[data-route-status]').textContent = message;
            container.querySelector('[data-open-route]').disabled = !(userPoint && jobPoint);
        },
    };
}

function clearRoute(map) {
    if (map.getLayer('kazilink-route-line')) map.removeLayer('kazilink-route-line');
    if (map.getLayer('kazilink-route-casing')) map.removeLayer('kazilink-route-casing');
    if (map.getSource('kazilink-route')) map.removeSource('kazilink-route');
}

async function drawRoute(map, routeState, userPoint, jobPoint) {
    clearRoute(map);
    routeState.panel.setRoute(userPoint, jobPoint);

    const userLngLat = toLngLat(userPoint);
    const jobLngLat = toLngLat(jobPoint);
    const url = `${OSRM_ROUTE_URL}/${userLngLat.join(',')};${jobLngLat.join(',')}?overview=full&geometries=geojson&steps=false`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`OSRM responded ${response.status}`);
        const data = await response.json();
        const route = data.routes && data.routes[0];
        if (!route) throw new Error('No OSRM route found');

        map.addSource('kazilink-route', {
            type: 'geojson',
            data: {
                type: 'Feature',
                geometry: route.geometry,
                properties: {},
            },
        });
        map.addLayer({
            id: 'kazilink-route-casing',
            type: 'line',
            source: 'kazilink-route',
            paint: {
                'line-color': '#ffffff',
                'line-width': 8,
                'line-opacity': 0.96,
            },
        });
        map.addLayer({
            id: 'kazilink-route-line',
            type: 'line',
            source: 'kazilink-route',
            paint: {
                'line-color': '#0f7cff',
                'line-width': 5,
                'line-opacity': 0.96,
            },
        });
        routeState.panel.setSummary(route.distance, route.duration);
        fitMap(map, [userPoint, jobPoint], jobPoint);
    } catch (error) {
        console.warn('Road route unavailable.', error);
        map.addSource('kazilink-route', {
            type: 'geojson',
            data: {
                type: 'Feature',
                geometry: {
                    type: 'LineString',
                    coordinates: [userLngLat, jobLngLat],
                },
                properties: {},
            },
        });
        map.addLayer({
            id: 'kazilink-route-line',
            type: 'line',
            source: 'kazilink-route',
            paint: {
                'line-color': '#0f7cff',
                'line-width': 4,
                'line-dasharray': [2, 2],
            },
        });
        routeState.panel.setMessage('Road route unavailable. Showing direct line.');
        fitMap(map, [userPoint, jobPoint], jobPoint);
    }
}

function showMessage(map, point, message) {
    new maplibregl.Popup({ closeOnClick: true })
        .setLngLat(toLngLat(point))
        .setHTML(message)
        .addTo(map);
}

function popupHtml(job) {
    const salary = job.salary ? `<br>KSh ${job.salary}` : '';
    const distance = job.distance !== null && job.distance !== undefined ? `<br>${job.distance} km away` : '';
    const source = job.sourceLabel ? `<br><small>${job.sourceLabel}</small>` : '';
    return `<strong>${job.title}</strong><br>${job.location}${salary}${distance}${source}<br><a href="${job.url}">View full job</a>`;
}

function createJobMarker(job, point, markerStore) {
    const marker = new maplibregl.Marker({ element: markerElement('job', 'Job'), anchor: 'bottom' })
        .setLngLat(toLngLat(point))
        .setPopup(new maplibregl.Popup({ offset: 26 }).setHTML(popupHtml(job)));
    markerStore.push(marker);
    return marker;
}

function createPointMarker(className, label, point, html, markerStore) {
    const marker = new maplibregl.Marker({ element: markerElement(className, label), anchor: 'bottom' })
        .setLngLat(toLngLat(point))
        .setPopup(new maplibregl.Popup({ offset: 26 }).setHTML(html));
    markerStore.push(marker);
    return marker;
}

function clearMarkers(markers) {
    markers.splice(0).forEach((marker) => marker.remove());
}

function haversineKm(fromPoint, toPoint) {
    const radius = 6371;
    const dlat = (toPoint[0] - fromPoint[0]) * Math.PI / 180;
    const dlng = (toPoint[1] - fromPoint[1]) * Math.PI / 180;
    const a = Math.sin(dlat / 2) ** 2
        + Math.cos(fromPoint[0] * Math.PI / 180) * Math.cos(toPoint[0] * Math.PI / 180) * Math.sin(dlng / 2) ** 2;
    return radius * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
}

function updateJobCardsForPlace(placePoint, radiusKm) {
    const rows = [];
    document.querySelectorAll('[data-job-card]').forEach((card) => {
        const job = window.kazilinkJobsById?.get(card.dataset.jobCard);
        const point = job ? normalizePoint(job.lat, job.lng, true) : null;
        if (!point) {
            card.hidden = true;
            return;
        }
        const distance = haversineKm(placePoint, point);
        const visible = distance <= radiusKm;
        card.hidden = !visible;
        card.dataset.placeDistance = distance.toFixed(3);
        const distanceNode = card.querySelector('[data-dynamic-distance]');
        if (distanceNode) distanceNode.textContent = `${distance.toFixed(1)} km from search`;
        if (visible) rows.push({ card, distance });
    });

    rows.sort((a, b) => a.distance - b.distance);
    const list = document.querySelector('.results-list');
    rows.forEach(({ card }) => list?.appendChild(card));
}

function placeDisplayName(feature) {
    const props = feature.properties || {};
    return [props.name, props.street, props.city || props.county, props.state, props.country]
        .filter(Boolean)
        .filter((value, index, values) => values.indexOf(value) === index)
        .join(', ');
}

async function photonSearch(query) {
    const params = new URLSearchParams({
        q: `${query} Kenya`,
        lang: 'en',
        limit: '6',
        lon: '36.9476',
        lat: '-0.4201',
    });
    const response = await fetch(`${PHOTON_URL}?${params.toString()}`);
    if (!response.ok) throw new Error('Photon search failed');
    const data = await response.json();
    return (data.features || []).filter((feature) => {
        const props = feature.properties || {};
        const coords = feature.geometry && feature.geometry.coordinates;
        return props.countrycode === 'KE' && coords && pointInKenya(coords[1], coords[0]);
    }).map((feature) => ({
        name: placeDisplayName(feature),
        lat: feature.geometry.coordinates[1],
        lng: feature.geometry.coordinates[0],
        type: feature.properties.osm_value || feature.properties.type || 'place',
    }));
}

async function nominatimSearch(query) {
    const params = new URLSearchParams({
        q: `${query}, Kenya`,
        format: 'jsonv2',
        limit: '6',
        countrycodes: 'ke',
        addressdetails: '1',
    });
    const response = await fetch(`${NOMINATIM_URL}?${params.toString()}`, {
        headers: { Accept: 'application/json' },
    });
    if (!response.ok) throw new Error('Nominatim search failed');
    const data = await response.json();
    return data.map((item) => ({
        name: item.display_name,
        lat: Number(item.lat),
        lng: Number(item.lon),
        type: item.type || item.class || 'place',
    })).filter((item) => pointInKenya(item.lat, item.lng));
}

async function serverGeocodeSearch(query) {
    const response = await fetch(`/api/geocode/?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('KaziLink geocoder failed');
    const data = await response.json();
    return (data.results || []).map((item) => ({
        name: item.name,
        lat: Number(item.lat),
        lng: Number(item.lng),
        type: item.type || 'place',
    })).filter((item) => pointInKenya(item.lat, item.lng));
}

async function searchPlaces(query) {
    try {
        const results = await serverGeocodeSearch(query);
        if (results.length) return results;
    } catch (error) {
        console.warn(error);
    }

    try {
        const results = await photonSearch(query);
        if (results.length) return results;
    } catch (error) {
        console.warn(error);
    }

    try {
        return await nominatimSearch(query);
    } catch (error) {
        console.warn(error);
        return [];
    }
}

function initPlaceSearch(map, jobs, markers, routeState) {
    const form = document.querySelector('[data-map-search-form]');
    const input = document.querySelector('[data-map-search-input]');
    const list = document.querySelector('[data-map-search-results]');
    const radius = document.querySelector('[data-map-radius]');
    if (!form || !input || !list || !radius) return;

    let selectedResults = [];
    let searchTimer = null;

    function renderResults(results) {
        list.innerHTML = '';
        list.hidden = !results.length;
        results.forEach((result, index) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.innerHTML = `<strong>${result.name}</strong><span>${result.type}</span>`;
            button.addEventListener('click', () => selectPlace(index));
            list.appendChild(button);
        });
    }

    function selectPlace(index) {
        const place = selectedResults[index];
        if (!place) return;
        const placePoint = [place.lat, place.lng];
        const radiusKm = Number(radius.value || 10);

        clearRoute(map);
        clearMarkers(markers);
        routeState.panel.setMessage(`Showing jobs within ${radiusKm} km of ${place.name}.`);

        createPointMarker('place', 'Place', placePoint, `<strong>${place.name}</strong><br>${place.type}`, markers).addTo(map);

        jobs.forEach((job) => {
            const point = normalizePoint(job.lat, job.lng, true);
            if (point && haversineKm(placePoint, point) <= radiusKm) {
                createJobMarker(job, point, markers).addTo(map);
            }
        });

        updateJobCardsForPlace(placePoint, radiusKm);
        map.flyTo({ center: [place.lng, place.lat], zoom: 17, duration: 900 });
        input.value = place.name;
        list.hidden = true;

        const url = new URL(window.location.href);
        url.searchParams.set('place', place.name);
        url.searchParams.set('place_lat', place.lat.toFixed(7));
        url.searchParams.set('place_lng', place.lng.toFixed(7));
        url.searchParams.set('radius', String(radiusKm));
        window.history.replaceState({}, '', url);
    }

    async function runSearch(query) {
        if (query.length < 3) {
            renderResults([]);
            return;
        }
        list.hidden = false;
        list.innerHTML = '<div class="map-search-empty">Searching places...</div>';
        selectedResults = await searchPlaces(query);
        renderResults(selectedResults);
        if (!selectedResults.length) {
            list.hidden = false;
            list.innerHTML = '<div class="map-search-empty">No Kenyan place found. Try a school, hospital, ward, road, or town.</div>';
        }
    }

    input.addEventListener('input', () => {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(() => runSearch(input.value.trim()), 300);
    });

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        if (selectedResults.length) {
            selectPlace(0);
            return;
        }
        runSearch(input.value.trim());
    });

    radius.addEventListener('change', () => {
        if (selectedResults.length) selectPlace(0);
    });

    const params = new URLSearchParams(window.location.search);
    const placeLat = Number(params.get('place_lat'));
    const placeLng = Number(params.get('place_lng'));
    const placeName = params.get('place');
    if (placeName && pointInKenya(placeLat, placeLng)) {
        input.value = placeName;
        selectedResults = [{ name: placeName, lat: placeLat, lng: placeLng, type: 'saved search' }];
        selectPlace(0);
    }
}

function initJobsMap() {
    const el = document.querySelector('#jobs-map');
    const dataEl = document.querySelector('#jobs-map-data');
    if (!el || !dataEl || !window.maplibregl) return;

    const jobs = JSON.parse(dataEl.textContent);
    const jobsById = new Map(jobs.map((job) => [String(job.id), job]));
    window.kazilinkJobsById = jobsById;

    const map = createMap(el);
    const markers = [];
    const routeState = { panel: createRoutePanel(map) };
    let userPoint = null;
    let selectedJobId = null;

    function addMarkers(job, jobPoint) {
        clearMarkers(markers);

        if (userPoint) {
            createPointMarker('you', 'You', userPoint, '<strong>You are here</strong><br>Your live GPS location', markers).addTo(map);
        }

        createJobMarker(job, jobPoint, markers).addTo(map).togglePopup();
    }

    function showJobOnMap(jobId) {
        const job = jobsById.get(String(jobId));
        const jobPoint = job ? normalizePoint(job.lat, job.lng, true) : null;
        if (!job || !jobPoint) {
            showMessage(map, [KENYA_CENTER[1], KENYA_CENTER[0]], 'This job has invalid GPS coordinates, so it cannot be shown on the map yet.');
            return;
        }

        selectedJobId = String(jobId);
        addMarkers(job, jobPoint);

        document.querySelectorAll('[data-job-card]').forEach((card) => {
            card.classList.toggle('is-selected', card.dataset.jobCard === String(jobId));
        });

        if (userPoint) {
            drawRoute(map, routeState, userPoint, jobPoint);
        } else {
            clearRoute(map);
            fitMap(map, [jobPoint], jobPoint);
            routeState.panel.setMessage('Allow GPS to calculate a road route.');
            showMessage(map, jobPoint, 'Please allow location access to show your live position and road route to this job.');
        }
    }

    function refreshLiveUserLocation() {
        getLiveUserPoint((point) => {
            userPoint = point;
            if (selectedJobId) {
                showJobOnMap(selectedJobId);
            } else {
                clearMarkers(markers);
                createPointMarker('you', 'You', userPoint, '<strong>You are here</strong><br>Your live GPS location', markers)
                    .addTo(map)
                    .togglePopup();
                fitMap(map, [userPoint], userPoint);
                routeState.panel.setMessage('Select a job to calculate the route.');
            }
        }, (message) => {
            routeState.panel.setMessage(message);
            showMessage(map, [KENYA_CENTER[1], KENYA_CENTER[0]], message);
        });
    }

    document.querySelectorAll('[data-map-job]').forEach((button) => {
        button.addEventListener('click', () => {
            selectedJobId = String(button.dataset.mapJob);
            showJobOnMap(selectedJobId);
            if (!userPoint) refreshLiveUserLocation();
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    });

    document.querySelectorAll('[data-job-card]').forEach((card) => {
        card.addEventListener('click', (event) => {
            if (event.target.closest('a, button')) return;
            selectedJobId = String(card.dataset.jobCard);
            showJobOnMap(selectedJobId);
            if (!userPoint) refreshLiveUserLocation();
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    });

    map.on('load', () => {
        initPlaceSearch(map, jobs, markers, routeState);
        const firstJobWithPoint = jobs.find((job) => normalizePoint(job.lat, job.lng, true));

        if (firstJobWithPoint) {
            const jobPoint = normalizePoint(firstJobWithPoint.lat, firstJobWithPoint.lng, true);
            jobs.forEach((job) => {
                const point = normalizePoint(job.lat, job.lng, true);
                if (point) createJobMarker(job, point, markers).addTo(map);
            });
            fitMap(map, [jobPoint], jobPoint);
            routeState.panel.setMessage('Search a place or select a job to calculate the route.');
        } else {
            fitMap(map, [], [KENYA_CENTER[1], KENYA_CENTER[0]]);
            routeState.panel.setMessage('No jobs with valid GPS coordinates are available.');
            showMessage(map, [KENYA_CENTER[1], KENYA_CENTER[0]], 'No jobs with valid GPS coordinates are available for this filter yet.');
        }
    });
}

function initJobDetailMap() {
    const el = document.querySelector('#job-detail-map');
    if (!el || !window.maplibregl) return;

    const jobPoint = normalizePoint(el.dataset.jobLat, el.dataset.jobLng, true);
    if (!jobPoint) return;

    const map = createMap(el, toLngLat(jobPoint), 17);
    const markers = [];
    const routeState = { panel: createRoutePanel(map) };

    function addJobMarker() {
        createJobMarker({
            title: el.dataset.jobTitle,
            location: el.dataset.jobLocation,
            url: window.location.href,
        }, jobPoint, markers).addTo(map);
    }

    function renderDetailRoute(userPoint) {
        clearMarkers(markers);
        addJobMarker();
        createPointMarker('you', 'You', userPoint, '<strong>You are here</strong><br>Your live GPS location', markers).addTo(map);
        drawRoute(map, routeState, userPoint, jobPoint);
    }

    map.on('load', () => {
        addJobMarker();
        fitMap(map, [jobPoint], jobPoint);
        getLiveUserPoint(renderDetailRoute, (message) => {
            routeState.panel.setMessage(message);
            showMessage(map, jobPoint, message);
        });
    });
}

initJobsMap();
initJobDetailMap();
