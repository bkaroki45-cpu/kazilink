import json
import math
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from .forms import (
    ActivityUpdateForm, ApplicationForm, CommentForm, JobAlertForm, JobForm, LoginForm,
    MessageForm, ProfileForm, RegisterForm, ReviewForm,
)
from .models import (
    Application, Category, Comment, Conversation, Follow, Job, JobAlert, JobLike, Message,
    Notification, Profile, Review, SavedJob,
)


def landing(request):
    stats = {
        'jobs': Job.objects.filter(status=Job.OPEN).count(),
        'employers': User.objects.filter(jobs__isnull=False).distinct().count(),
        'seekers': Profile.objects.count(),
    }
    featured_jobs = Job.objects.filter(status=Job.OPEN).select_related('category', 'employer')[:3]
    return render(request, 'marketplace/landing.html', {'stats': stats, 'featured_jobs': featured_jobs})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            Profile.objects.create(user=user, role=Profile.SEEKER)
            login(request, user)
            messages.success(request, 'Welcome to KaziLink. Your profile is ready.')
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('feed')
    else:
        form = RegisterForm()
    return render(request, 'marketplace/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('feed')
    else:
        form = LoginForm()
    return render(request, 'marketplace/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('landing')


def _open_jobs():
    return Job.objects.filter(status=Job.OPEN).select_related('employer', 'employer__profile', 'category')


KENYA_BOUNDS = {
    'lat_min': -4.9,
    'lat_max': 5.3,
    'lng_min': 33.5,
    'lng_max': 42.1,
}


KENYA_PLACE_COORDINATES = {
    'baringo': (0.4897, 35.7412),
    'bungoma': (0.5635, 34.5606),
    'busia': (0.4608, 34.1115),
    'eldoret': (0.5143, 35.2698),
    'embu': (-0.5399, 37.4574),
    'garissa': (-0.4536, 39.6401),
    'homa bay': (-0.5273, 34.4571),
    'isiolo': (0.3546, 37.5822),
    'kajiado': (-1.8524, 36.7768),
    'kakamega': (0.2827, 34.7519),
    'kericho': (-0.3677, 35.2831),
    'kiambu': (-1.1714, 36.8356),
    'kilifi': (-3.6305, 39.8499),
    'kisii': (-0.6773, 34.7796),
    'kisumu': (-0.0917, 34.7680),
    'kitale': (1.0157, 35.0062),
    'kitui': (-1.3751, 38.0106),
    'kwale': (-4.1816, 39.4606),
    'laikipia': (0.3606, 36.7819),
    'lamu': (-2.2696, 40.9006),
    'machakos': (-1.5177, 37.2634),
    'makueni': (-1.8039, 37.6242),
    'malindi': (-3.2192, 40.1169),
    'mandera': (3.9373, 41.8569),
    'meru': (0.0470, 37.6498),
    'migori': (-1.0634, 34.4731),
    'mombasa': (-4.0435, 39.6682),
    'muranga': (-0.7210, 37.1526),
    'nairobi': (-1.2864, 36.8172),
    'nakuru': (-0.3031, 36.0800),
    'nandi': (0.1836, 35.1269),
    'narok': (-1.0875, 35.8711),
    'naivasha': (-0.7138, 36.4326),
    'nyahururu': (0.0381, 36.3634),
    'nyamira': (-0.5669, 34.9358),
    'nyandarua': (-0.1804, 36.5226),
    'nyeri': (-0.4201, 36.9476),
    'siaya': (0.0612, 34.2882),
    'thika': (-1.0333, 37.0693),
    'trans nzoia': (1.0567, 34.9507),
    'turkana': (3.3122, 35.5658),
    'uasin gishu': (0.5528, 35.3027),
    'vihiga': (0.0768, 34.7258),
    'wajir': (1.7471, 40.0573),
}


PLACE_ALIASES = {
    'tti': 'technical training institute',
    'ttc': 'teachers training college',
    'tvc': 'technical and vocational college',
    'poly': 'polytechnic',
    'uni': 'university',
    'univ': 'university',
    'hosp': 'hospital',
    'sch': 'school',
}


KNOWN_PLACE_HINTS = {
    'mathenge': [
        'Mathenge Technical Training Institute, Othaya, Nyeri, Kenya',
        'Mathenge TTI, Othaya, Nyeri, Kenya',
        'Mathenge, Othaya, Nyeri, Kenya',
    ],
    'dedan kimathi': [
        'Dedan Kimathi University of Technology, Nyeri, Kenya',
        'Dedan Kimathi University, Nyeri, Kenya',
    ],
    'nyeri county referral hospital': [
        'Nyeri County Referral Hospital, Nyeri, Kenya',
        'PGH Nyeri, Nyeri, Kenya',
    ],
    'nyeri bus station': [
        'Nyeri Bus Station, Nyeri, Kenya',
        'Nyeri Bus Park, Nyeri, Kenya',
    ],
    'mahiga': [
        'Mahiga Ward, Othaya, Nyeri, Kenya',
        'Mahiga, Nyeri, Kenya',
    ],
}


KNOWN_POI_COORDINATES = {
    'mathenge technical training institute': {
        'lat': -0.508492,
        'lng': 36.891917,
        'name': 'Mathenge Technical Training Institute, Mahiga, Othaya, Nyeri, Kenya',
    },
    'mathenge tti': {
        'lat': -0.508492,
        'lng': 36.891917,
        'name': 'Mathenge Technical Training Institute, Mahiga, Othaya, Nyeri, Kenya',
    },
    'mathenge technical institute': {
        'lat': -0.508492,
        'lng': 36.891917,
        'name': 'Mathenge Technical Training Institute, Mahiga, Othaya, Nyeri, Kenya',
    },
}


def _point_in_kenya(latitude, longitude):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return False
    return (
        KENYA_BOUNDS['lat_min'] <= latitude <= KENYA_BOUNDS['lat_max']
        and KENYA_BOUNDS['lng_min'] <= longitude <= KENYA_BOUNDS['lng_max']
    )


def _clean_kenya_point(latitude, longitude):
    if _point_in_kenya(latitude, longitude):
        return float(latitude), float(longitude)
    if _point_in_kenya(longitude, latitude):
        return float(longitude), float(latitude)
    return None


def _positive_float(value, default=None):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


def normalize_location_text(value):
    value = (value or '').strip().lower()
    value = re.sub(r'[\.,;:/\\|()\[\]{}]+', ' ', value)
    value = re.sub(r'\s+', ' ', value)
    words = [PLACE_ALIASES.get(word, word) for word in value.split()]
    return ' '.join(words)


def _location_query_variants(location):
    location_text = (location or '').strip()
    normalized = normalize_location_text(location_text)
    if not normalized:
        return []

    variants = []

    for key, hints in KNOWN_PLACE_HINTS.items():
        if key in normalized:
            variants.extend(hints)

    variants.extend([
        location_text,
        f'{location_text}, Kenya',
        f'{location_text}, Nyeri, Kenya',
        f'{location_text}, Othaya, Nyeri, Kenya',
    ])

    expanded = normalized.title()
    if expanded and expanded != location_text:
        variants.extend([
            expanded,
            f'{expanded}, Kenya',
            f'{expanded}, Othaya, Nyeri, Kenya',
        ])

    seen = set()
    unique = []
    for query in variants:
        key = normalize_location_text(query)
        if key and key not in seen:
            unique.append(query)
            seen.add(key)
    return unique


def _place_rank(result, original_query, provider):
    lat = result.get('lat')
    lng = result.get('lon') or result.get('lng')
    if not _point_in_kenya(lat, lng):
        return -999

    display = normalize_location_text(result.get('display_name') or result.get('name') or '')
    original = normalize_location_text(original_query)
    score = 0

    if provider == 'nominatim':
        score += 25
    if 'kenya' in display:
        score += 40
    if 'nyeri' in display:
        score += 18
    if 'othaya' in display:
        score += 14
    if original and original in display:
        score += 35

    original_words = set(original.split())
    display_words = set(display.split())
    score += len(original_words & display_words) * 8

    place_type = normalize_location_text(result.get('type') or result.get('class') or result.get('osm_value') or '')
    if place_type in {'school', 'college', 'university', 'hospital', 'bus station', 'station', 'commercial', 'road', 'village', 'administrative'}:
        score += 12

    importance = result.get('importance')
    if importance is not None:
        try:
            score += float(importance) * 10
        except (TypeError, ValueError):
            pass

    return score


def _fetch_json(url, user_agent=True):
    headers = {'User-Agent': 'KaziLink/1.0 local job geocoder'} if user_agent else {}
    with urlopen(Request(url, headers=headers), timeout=6) as response:
        return json.loads(response.read().decode('utf-8'))


def _debug_geocoder(label, value):
    try:
        print(label, json.dumps(value, ensure_ascii=True)[:2000])
    except TypeError:
        print(label, repr(value).encode('ascii', 'backslashreplace').decode('ascii')[:2000])


def _nominatim_search(query, limit=5):
    _debug_geocoder('Search query:', query)
    params = urlencode({
        'q': query,
        'format': 'jsonv2',
        'limit': limit,
        'countrycodes': 'ke',
        'addressdetails': 1,
        'extratags': 1,
        'namedetails': 1,
    })

    try:
        results = _fetch_json(f'https://nominatim.openstreetmap.org/search?{params}')
    except Exception as error:
        _debug_geocoder('Geocoder result:', {'provider': 'nominatim', 'error': str(error)})
        return []

    _debug_geocoder('Geocoder result:', results[:2] if isinstance(results, list) else results)
    return [
        {
            'lat': item.get('lat'),
            'lon': item.get('lon'),
            'display_name': item.get('display_name', ''),
            'type': item.get('type', ''),
            'class': item.get('class', ''),
            'importance': item.get('importance'),
            'provider': 'nominatim',
        }
        for item in results
    ]


def _photon_search(query, limit=5):
    _debug_geocoder('Search query:', query)
    params = urlencode({
        'q': query,
        'limit': limit,
        'lang': 'en',
        'lat': -0.4201,
        'lon': 36.9476,
    })

    try:
        data = _fetch_json(f'https://photon.komoot.io/api/?{params}', user_agent=False)
    except Exception as error:
        _debug_geocoder('Geocoder result:', {'provider': 'photon', 'error': str(error)})
        return []

    features = data.get('features', []) if isinstance(data, dict) else []
    _debug_geocoder('Geocoder result:', features[:2])
    results = []
    for feature in features:
        props = feature.get('properties', {})
        coords = feature.get('geometry', {}).get('coordinates') or []
        if len(coords) < 2 or props.get('countrycode') != 'KE':
            continue
        name_parts = [
            props.get('name'),
            props.get('street'),
            props.get('city'),
            props.get('county'),
            props.get('state'),
            props.get('country'),
        ]
        results.append({
            'lat': coords[1],
            'lon': coords[0],
            'display_name': ', '.join([part for part in name_parts if part]),
            'type': props.get('osm_value') or props.get('type') or '',
            'class': props.get('osm_key') or '',
            'provider': 'photon',
        })
    return results


def geocode_kenya_suggestions(location, limit=6):
    candidates = []
    normalized = normalize_location_text(location)
    for place, point in KNOWN_POI_COORDINATES.items():
        if normalized in place or place in normalized:
            candidates.append({
                'lat': point['lat'],
                'lon': point['lng'],
                'display_name': point['name'],
                'type': 'college',
                'class': 'amenity',
                'provider': 'local',
                'importance': 1,
            })

    for query in _location_query_variants(location):
        candidates.extend(_nominatim_search(query, limit=limit))
        if len(candidates) >= limit:
            break

    if len(candidates) < limit:
        for query in _location_query_variants(location):
            candidates.extend(_photon_search(query, limit=limit))
            if len(candidates) >= limit:
                break

    unique = []
    seen = set()
    for result in candidates:
        point = _clean_kenya_point(result.get('lat'), result.get('lon'))
        if not point:
            continue
        key = (round(point[0], 5), round(point[1], 5), normalize_location_text(result.get('display_name')))
        if key in seen:
            continue
        seen.add(key)
        result['lat'] = point[0]
        result['lng'] = point[1]
        result['score'] = _place_rank(result, location, result.get('provider'))
        unique.append(result)

    unique.sort(key=lambda item: item.get('score', 0), reverse=True)
    return unique[:limit]


def geocode_kenya_location(location):
    normalized = normalize_location_text(location)
    if not normalized:
        return None

    for place, point in KNOWN_POI_COORDINATES.items():
        if normalized in place or place in normalized:
            _debug_geocoder('Search query:', location)
            _debug_geocoder('Geocoder result:', point)
            return {
                'lat': point['lat'],
                'lng': point['lng'],
                'name': point['name'],
                'provider': 'local',
                'score': 150,
            }

    for place, point in KENYA_PLACE_COORDINATES.items():
        if place == normalized or place in normalized:
            return {
                'lat': point[0],
                'lng': point[1],
                'name': place.title(),
                'provider': 'local',
                'score': 100,
            }

    suggestions = geocode_kenya_suggestions(location, limit=8)
    if not suggestions:
        return None

    best = suggestions[0]
    return {
        'lat': best['lat'],
        'lng': best['lng'],
        'name': best.get('display_name') or location,
        'provider': best.get('provider', ''),
        'score': best.get('score', 0),
    }


def resolve_job_coordinates(job):
    exact_point = _clean_kenya_point(job.latitude, job.longitude)
    if exact_point:
        return {
            'lat': exact_point[0],
            'lng': exact_point[1],
            'source': 'gps',
            'label': job.resolved_place_name or job.location or 'GPS verified',
        }

    geocoded = geocode_kenya_location(job.location)
    if geocoded:
        return {
            'lat': geocoded['lat'],
            'lng': geocoded['lng'],
            'source': geocoded.get('provider') or 'geocoded',
            'label': geocoded.get('name') or 'Geocoded from location',
        }

    return None


def job_map_point(job):
    point = _clean_kenya_point(job.latitude, job.longitude)
    if point:
        return {
            'lat': point[0],
            'lng': point[1],
            'source': 'gps',
            'label': 'Saved job coordinates',
        }

    return None


def ensure_job_coordinates(job):
    point = job_map_point(job)
    if point:
        return point

    resolved = resolve_job_coordinates(job)
    if not resolved:
        return None

    job.latitude = resolved['lat']
    job.longitude = resolved['lng']
    job.resolved_place_name = resolved['label']
    job.save(update_fields=['latitude', 'longitude', 'resolved_place_name'])
    return {
        'lat': resolved['lat'],
        'lng': resolved['lng'],
        'source': resolved['source'],
        'label': resolved['label'],
    }


def alert_matches_job(alert, job):
    if not alert.active or job.status != Job.OPEN:
        return False
    if alert.keyword:
        haystack = f'{job.title} {job.description} {job.required_skills}'.lower()
        if alert.keyword.lower() not in haystack:
            return False
    if alert.category_id and job.category_id != alert.category_id:
        return False
    if alert.job_type and job.job_type != alert.job_type:
        return False
    if alert.salary_min and (not job.salary or job.salary < alert.salary_min):
        return False
    if alert.salary_max and (not job.salary or job.salary > alert.salary_max):
        return False
    if alert.latitude and alert.longitude:
        point = ensure_job_coordinates(job)
        if not point:
            return False
        return distance_km(alert.latitude, alert.longitude, point['lat'], point['lng']) <= alert.radius_km
    if alert.location:
        return alert.location.lower() in (job.location or '').lower()
    return True


def matching_alert_jobs(user):
    alerts = list(user.job_alerts.filter(active=True).select_related('category'))
    if not alerts:
        return []

    matches = []
    seen = set()
    for job in _open_jobs():
        for alert in alerts:
            if alert_matches_job(alert, job):
                if job.id not in seen:
                    matches.append(job)
                    seen.add(job.id)
                break
    return matches


def notify_matching_alerts(job):
    for alert in JobAlert.objects.filter(active=True).select_related('user', 'category'):
        if alert.user_id == job.employer_id:
            continue
        if alert_matches_job(alert, job):
            Notification.objects.create(
                user=alert.user,
                title='New job alert match',
                body=f'{job.title} matches your saved alert near {alert.location or job.location}.',
                url=job.get_absolute_url(),
            )


@login_required
def feed(request):
    jobs = _open_jobs().annotate(like_count=Count('likes'), comment_count=Count('comments')).order_by('-created_at')
    paginator = Paginator(jobs, 8)
    page_obj = paginator.get_page(request.GET.get('page'))
    trending = _open_jobs().annotate(app_count=Count('applications')).order_by('-app_count', '-created_at')[:5]
    saved_ids = set(SavedJob.objects.filter(user=request.user).values_list('job_id', flat=True))
    liked_ids = set(JobLike.objects.filter(user=request.user).values_list('job_id', flat=True))
    return render(request, 'marketplace/feed.html', {
        'page_obj': page_obj,
        'trending': trending,
        'saved_ids': saved_ids,
        'liked_ids': liked_ids,
        'update_form': ActivityUpdateForm(),
    })


@login_required
def post_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user
            point = resolve_job_coordinates(job)
            if not point:
                form.add_error('location', 'We could not find GPS coordinates for this location. Use the GPS button or enter a clearer Kenyan town/area.')
                return render(request, 'marketplace/post_job.html', {'form': form})
            job.latitude = point['lat']
            job.longitude = point['lng']
            job.resolved_place_name = point['label']
            job.save()
            Notification.objects.create(
                user=request.user,
                title='Job posted',
                body=f'{job.title} is now visible while open.',
                url=job.get_absolute_url(),
            )
            notify_matching_alerts(job)
            messages.success(request, 'Your job is live on KaziLink.')
            return redirect(job)
    else:
        form = JobForm()
    return render(request, 'marketplace/post_job.html', {'form': form})


@login_required
def find_jobs(request):
    jobs = _open_jobs()
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    location = request.GET.get('location', '').strip()
    job_type = request.GET.get('job_type', '')
    salary_min = request.GET.get('salary_min', '')
    salary_max = request.GET.get('salary_max', '')
    sort = request.GET.get('sort', 'latest')
    nearby = request.GET.get('nearby')
    place_point = _clean_kenya_point(request.GET.get('place_lat'), request.GET.get('place_lng'))
    radius_km = _positive_float(request.GET.get('radius'), 10)

    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(required_skills__icontains=query))
    if category:
        jobs = jobs.filter(category_id=category)
    if location and not place_point:
        jobs = jobs.filter(location__icontains=location)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if salary_min:
        jobs = jobs.filter(salary__gte=salary_min)
    if salary_max:
        jobs = jobs.filter(salary__lte=salary_max)
    if place_point:
        jobs = list(jobs)
        filtered_jobs = []
        for job in jobs:
            point = ensure_job_coordinates(job)
            job.map_point = point
            if point:
                job.distance = round(distance_km(place_point[0], place_point[1], point['lat'], point['lng']), 1)
                if job.distance <= radius_km:
                    filtered_jobs.append(job)
            else:
                job.distance = None
        jobs = sorted(filtered_jobs, key=lambda item: item.created_at, reverse=True)
    elif nearby and request.user.profile.latitude and request.user.profile.longitude:
        jobs = list(jobs)
        for job in jobs:
            point = ensure_job_coordinates(job)
            job.map_point = point
            if point:
                job.distance = round(distance_km(request.user.profile.latitude, request.user.profile.longitude, point['lat'], point['lng']), 1)
            else:
                job.distance = None
        jobs.sort(key=lambda item: item.created_at, reverse=True)
    elif sort == 'popular':
        jobs = jobs.annotate(app_count=Count('applications')).order_by('-app_count')
    else:
        jobs = jobs.order_by('-created_at')

    return render(request, 'marketplace/find_jobs.html', {
        'jobs': jobs,
        'user_latitude': float(request.user.profile.latitude) if request.user.profile.latitude else None,
        'user_longitude': float(request.user.profile.longitude) if request.user.profile.longitude else None,
        'categories': Category.objects.all(),
        'job_types': Job.TYPE_CHOICES,
        'alert_form': JobAlertForm(initial={
            'keyword': query,
            'category': category or None,
            'job_type': job_type,
            'location': request.GET.get('place') or location,
            'latitude': request.GET.get('place_lat') or None,
            'longitude': request.GET.get('place_lng') or None,
            'radius_km': request.GET.get('radius') or 20,
            'salary_min': salary_min,
            'salary_max': salary_max,
        }),
        'filters': request.GET,
    })


@login_required
@require_POST
def create_job_alert(request):
    form = JobAlertForm(request.POST)
    if form.is_valid():
        alert = form.save(commit=False)
        alert.user = request.user
        if alert.location and not (alert.latitude and alert.longitude):
            point = geocode_kenya_location(alert.location)
            if point:
                alert.latitude = point['lat']
                alert.longitude = point['lng']
                alert.location = point['name']
        alert.save()
        count = len(matching_alert_jobs(request.user))
        messages.success(request, f'Job alert saved. {count} current open jobs match your alerts.')
    else:
        messages.error(request, 'Please check the alert details and try again.')
    return redirect('find_jobs')


@login_required
@require_GET
def geocode_api(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    results = geocode_kenya_suggestions(query, limit=6)
    return JsonResponse({
        'results': [
            {
                'name': item.get('display_name') or query,
                'lat': item['lat'],
                'lng': item['lng'],
                'type': item.get('type') or item.get('class') or item.get('provider') or 'place',
                'score': item.get('score', 0),
            }
            for item in results
        ],
    })


@login_required
def job_detail(request, pk):
    job = get_object_or_404(Job.objects.select_related('employer', 'employer__profile', 'category'), pk=pk)
    if job.status != Job.OPEN and job.employer != request.user:
        messages.info(request, 'That job is no longer available.')
        return redirect('feed')
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.job = job
            comment.save()
            if request.user != job.employer:
                Notification.objects.create(user=job.employer, title='New comment', body=job.title, url=job.get_absolute_url())
            return redirect(job)
    job.views = job.views + 1
    job.save(update_fields=['views'])
    employer_followed = False
    if request.user != job.employer:
        employer_followed = Follow.objects.filter(follower=request.user, followed=job.employer).exists()
    map_point = ensure_job_coordinates(job)
    applications = []
    if request.user == job.employer:
        applications = job.applications.select_related('applicant', 'applicant__profile').order_by('-created_at')
    return render(request, 'marketplace/job_detail.html', {
        'job': job,
        'comment_form': CommentForm(),
        'application_form': ApplicationForm(),
        'applications': applications,
        'has_applied': Application.objects.filter(job=job, applicant=request.user).exists(),
        'is_saved': SavedJob.objects.filter(job=job, user=request.user).exists(),
        'is_liked': JobLike.objects.filter(job=job, user=request.user).exists(),
        'is_following_employer': employer_followed,
        'status_choices': Job.STATUS_CHOICES,
        'job_latitude': map_point['lat'] if map_point else None,
        'job_longitude': map_point['lng'] if map_point else None,
        'job_location_source': map_point['label'] if map_point else '',
        'user_latitude': float(request.user.profile.latitude) if request.user.profile.latitude else None,
        'user_longitude': float(request.user.profile.longitude) if request.user.profile.longitude else None,
    })


@login_required
@require_POST
def update_job_status(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    status = request.POST.get('status')
    if status in dict(Job.STATUS_CHOICES):
        job.status = status
        job.save(update_fields=['status'])
        messages.success(request, f'Job status updated to {job.get_status_display()}.')
    return redirect(job)


@login_required
@require_POST
def toggle_like(request, pk):
    job = get_object_or_404(Job, pk=pk, status=Job.OPEN)
    like, created = JobLike.objects.get_or_create(user=request.user, job=job)
    if not created:
        like.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        active = created
        return JsonResponse({
            'active': active,
            'label': 'Liked' if active else 'Like',
            'count': job.likes.count(),
        })
    return redirect(request.POST.get('next') or 'feed')


@login_required
@require_POST
def toggle_save(request, pk):
    job = get_object_or_404(Job, pk=pk, status=Job.OPEN)
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        saved.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        active = created
        return JsonResponse({
            'active': active,
            'label': 'Saved' if active else 'Save',
            'count': job.saves.count(),
        })
    return redirect(request.POST.get('next') or 'feed')


@login_required
@require_POST
def apply_job(request, pk):
    job = get_object_or_404(Job, pk=pk, status=Job.OPEN)
    if request.user == job.employer:
        messages.error(request, 'You cannot apply to your own job.')
        return redirect(job)
    form = ApplicationForm(request.POST)
    if form.is_valid():
        application, created = Application.objects.get_or_create(
            applicant=request.user,
            job=job,
            defaults={'message': form.cleaned_data['message']},
        )
        if created:
            Notification.objects.create(user=job.employer, title='New application', body=f'{request.user.username} applied to {job.title}', url=job.get_absolute_url())
            messages.success(request, 'Application sent.')
        else:
            messages.info(request, 'You have already applied.')
    return redirect(job)


@login_required
def profile_detail(request, username):
    profile_user = get_object_or_404(User.objects.select_related('profile'), username=username)
    jobs = Job.objects.filter(employer=profile_user)
    if request.user != profile_user:
        jobs = jobs.filter(status=Job.OPEN)
    jobs = jobs[:6]
    reviews = Review.objects.filter(reviewed=profile_user).select_related('reviewer')
    updates = profile_user.updates.all()[:5]
    return render(request, 'marketplace/profile.html', {
        'profile_user': profile_user,
        'jobs': jobs,
        'reviews': reviews,
        'updates': updates,
        'is_following': Follow.objects.filter(follower=request.user, followed=profile_user).exists(),
        'update_form': ActivityUpdateForm(),
    })


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile_detail', username=request.user.username)
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'marketplace/edit_profile.html', {'form': form})


@login_required
def settings_view(request):
    return render(request, 'marketplace/settings.html')


@login_required
def review_user(request, username):
    reviewed = get_object_or_404(User, username=username)
    if request.method == 'POST' and reviewed != request.user:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review, _ = Review.objects.update_or_create(
                reviewer=request.user,
                reviewed=reviewed,
                defaults=form.cleaned_data,
            )
            Notification.objects.create(user=reviewed, title='New review', body=f'{request.user.username} reviewed you.', url=reverse('profile_detail', kwargs={'username': reviewed.username}))
            messages.success(request, 'Review published.')
    return redirect('profile_detail', username=username)


@login_required
@require_POST
def toggle_follow(request, username):
    followed = get_object_or_404(User, username=username)
    if followed != request.user:
        follow, created = Follow.objects.get_or_create(follower=request.user, followed=followed)
        if not created:
            follow.delete()
    return redirect(request.POST.get('next') or reverse('profile_detail', kwargs={'username': username}))


@login_required
def inbox(request):
    conversations = request.user.conversations.prefetch_related('participants', 'messages')
    conversation_list = list(conversations)
    for conversation in conversation_list:
        conversation.other_user = next((participant for participant in conversation.participants.all() if participant != request.user), None)
        conversation.latest_message = conversation.messages.last()
        conversation.unread_count = conversation.messages.filter(seen=False).exclude(sender=request.user).count()
    return render(request, 'marketplace/inbox.html', {'conversations': conversation_list})


@login_required
def start_conversation(request, username):
    other = get_object_or_404(User, username=username)
    if other == request.user:
        messages.info(request, 'Open a job seeker profile or job post to message someone directly.')
        return redirect('inbox')
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other).first()
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other)
    return redirect('chat_room', conversation_id=conversation.id)


@login_required
def chat_room(request, conversation_id):
    conversation = get_object_or_404(Conversation.objects.prefetch_related('participants', 'messages'), id=conversation_id, participants=request.user)
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conversation
            msg.sender = request.user
            msg.save()
            conversation.save()
            for participant in conversation.participants.exclude(id=request.user.id):
                Notification.objects.create(user=participant, title='New message', body=request.user.username, url=reverse('chat_room', kwargs={'conversation_id': conversation.id}))
            return redirect('chat_room', conversation_id=conversation.id)
    Message.objects.filter(conversation=conversation).exclude(sender=request.user).update(seen=True)
    return render(request, 'marketplace/chat.html', {'conversation': conversation, 'message_form': MessageForm()})


@login_required
def chat_messages_api(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    Message.objects.filter(conversation=conversation).exclude(sender=request.user).update(seen=True)
    messages_payload = [
        {
            'id': message.id,
            'sender': message.sender.username,
            'mine': message.sender_id == request.user.id,
            'body': message.body,
            'image': message.image.url if message.image else '',
            'voice_note': message.voice_note.url if message.voice_note else '',
            'attachment': message.attachment.url if message.attachment else '',
            'time': message.created_at.strftime('%H:%M'),
            'seen': message.seen,
        }
        for message in conversation.messages.select_related('sender')
    ]
    return JsonResponse({'messages': messages_payload})


@login_required
def notifications(request):
    alert_jobs = matching_alert_jobs(request.user)
    notes = request.user.notifications.all()
    unread = notes.filter(read=False)
    unread.update(read=True)
    return render(request, 'marketplace/notifications.html', {
        'notifications': notes,
        'alert_jobs': alert_jobs,
        'job_alerts': request.user.job_alerts.filter(active=True),
    })


@login_required
def jobs_api(request):
    jobs = list(_open_jobs()[:20].values('id', 'title', 'location', 'salary', 'latitude', 'longitude', 'created_at'))
    return JsonResponse({'jobs': jobs})


@login_required
@require_POST
def update_location(request):
    profile = request.user.profile
    profile.latitude = request.POST.get('latitude') or None
    profile.longitude = request.POST.get('longitude') or None
    profile.save(update_fields=['latitude', 'longitude'])
    return JsonResponse({'ok': True})


def distance_km(lat1, lon1, lat2, lon2):
    radius = 6371
    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon / 2) ** 2
    return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
