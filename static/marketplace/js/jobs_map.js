const satelliteLayer = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
const labelLayer = 'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}';

function markerIcon(className, label) {
    return L.divIcon({
        className: `map-pin ${className}`,
        html: `<span>${label}</span>`,
        iconSize: [38, 38],
        iconAnchor: [19, 34],
        popupAnchor: [0, -30],
    });
}

function addAerialLayers(map) {
    L.tileLayer(satelliteLayer, { maxZoom: 19, attribution: 'Tiles &copy; Esri' }).addTo(map);
    L.tileLayer(labelLayer, { maxZoom: 19, attribution: 'Labels &copy; Esri' }).addTo(map);
}

function validPoint(lat, lng) {
    return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
}

function fitMap(map, points, fallback) {
    if (points.length > 1) {
        map.fitBounds(L.latLngBounds(points), { padding: [42, 42], maxZoom: 15 });
    } else if (points.length === 1) {
        map.setView(points[0], 15);
    } else {
        map.setView(fallback, 12);
    }
    window.setTimeout(() => map.invalidateSize(), 150);
    if (!map._kazilinkResizeBound) {
        window.addEventListener('resize', () => map.invalidateSize());
        map._kazilinkResizeBound = true;
    }
}

function initJobsMap() {
    const el = document.querySelector('#jobs-map');
    const dataEl = document.querySelector('#jobs-map-data');
    if (!el || !dataEl || !window.L) return;

    const jobs = JSON.parse(dataEl.textContent);
    const jobsById = new Map(jobs.map((job) => [String(job.id), job]));
    const userLat = Number(el.dataset.userLat);
    const userLng = Number(el.dataset.userLng);
    const map = L.map(el, { zoomControl: true });
    addAerialLayers(map);

    const selectedLayer = L.layerGroup().addTo(map);
    let userPoint = null;
    if (validPoint(userLat, userLng)) {
        userPoint = [userLat, userLng];
        L.marker(userPoint, { icon: markerIcon('you', 'You') })
            .addTo(selectedLayer)
            .bindPopup('<strong>You are here</strong><br>Your saved GPS location');
    }

    function showJobOnMap(jobId) {
        const job = jobsById.get(String(jobId));
        if (!job || !validPoint(Number(job.lat), Number(job.lng))) return;

        selectedLayer.clearLayers();
        const jobPoint = [Number(job.lat), Number(job.lng)];
        const points = [jobPoint];

        if (userPoint) {
            points.push(userPoint);
            L.marker(userPoint, { icon: markerIcon('you', 'You') })
                .addTo(selectedLayer)
                .bindPopup('<strong>You are here</strong><br>Your saved GPS location');
            L.polyline([userPoint, jobPoint], { color: '#0f7cff', weight: 4, opacity: 0.85, dashArray: '10 8' })
                .addTo(selectedLayer);
        }

        const salary = job.salary ? `<br>KSh ${job.salary}` : '';
        const distance = job.distance !== null && job.distance !== undefined ? `<br>${job.distance} km away` : '';
        L.marker(jobPoint, { icon: markerIcon('job', 'Job') })
            .addTo(selectedLayer)
            .bindPopup(`<strong>${job.title}</strong><br>${job.location}${salary}${distance}<br><a href="${job.url}">View full job</a>`)
            .openPopup();

        document.querySelectorAll('[data-job-card]').forEach((card) => {
            card.classList.toggle('is-selected', card.dataset.jobCard === String(jobId));
        });

        fitMap(map, points, jobPoint);
    }

    document.querySelectorAll('[data-map-job]').forEach((button) => {
        button.addEventListener('click', () => {
            showJobOnMap(button.dataset.mapJob);
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    });

    document.querySelectorAll('[data-job-card]').forEach((card) => {
        card.addEventListener('click', (event) => {
            if (event.target.closest('a, button')) return;
            showJobOnMap(card.dataset.jobCard);
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    });

    const firstJobWithPoint = jobs.find((job) => {
        if (!validPoint(Number(job.lat), Number(job.lng))) return;
        return true;
    });

    if (userPoint) {
        fitMap(map, [userPoint], userPoint);
        L.popup()
            .setLatLng(userPoint)
            .setContent(firstJobWithPoint ? 'Select a job card to see its exact location and route.' : 'No jobs with GPS coordinates are available for this filter yet.')
            .openOn(map);
    } else if (firstJobWithPoint) {
        const jobPoint = [Number(firstJobWithPoint.lat), Number(firstJobWithPoint.lng)];
        fitMap(map, [jobPoint], jobPoint);
        L.popup()
            .setLatLng(jobPoint)
            .setContent('Use GPS, then select a job to show your position and route.')
            .openOn(map);
    } else {
        fitMap(map, [], [-1.286389, 36.817223]);
        L.popup()
            .setLatLng([-1.286389, 36.817223])
            .setContent('No jobs with GPS coordinates are available for this filter yet.')
            .openOn(map);
    }
}

function initJobDetailMap() {
    const el = document.querySelector('#job-detail-map');
    if (!el || !window.L) return;

    const jobLat = Number(el.dataset.jobLat);
    const jobLng = Number(el.dataset.jobLng);
    const userLat = Number(el.dataset.userLat);
    const userLng = Number(el.dataset.userLng);
    if (!validPoint(jobLat, jobLng)) return;

    const jobPoint = [jobLat, jobLng];
    const map = L.map(el, { zoomControl: true });
    addAerialLayers(map);

    const points = [jobPoint];
    L.marker(jobPoint, { icon: markerIcon('job', 'Job') })
        .addTo(map)
        .bindPopup(`<strong>${el.dataset.jobTitle}</strong><br>${el.dataset.jobLocation}`);

    if (validPoint(userLat, userLng)) {
        const userPoint = [userLat, userLng];
        points.push(userPoint);
        L.marker(userPoint, { icon: markerIcon('you', 'You') }).addTo(map).bindPopup('<strong>You are here</strong><br>Your saved GPS location');
        L.polyline([userPoint, jobPoint], { color: '#0f7cff', weight: 4, opacity: 0.85, dashArray: '10 8' }).addTo(map);
    } else {
        L.popup()
            .setLatLng(jobPoint)
            .setContent('Refresh GPS to show your position and route to this job.')
            .openOn(map);
    }

    fitMap(map, points, jobPoint);
}

initJobsMap();
initJobDetailMap();
