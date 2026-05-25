import math

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    ActivityUpdateForm, ApplicationForm, CommentForm, JobForm, LoginForm,
    MessageForm, ProfileForm, RegisterForm, ReviewForm,
)
from .models import (
    Application, Category, Comment, Conversation, Follow, Job, JobLike, Message,
    Notification, Profile, Review, SavedJob,
)


def landing(request):
    if request.user.is_authenticated:
        return redirect('feed')
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
            return redirect('feed')
    else:
        form = RegisterForm()
    return render(request, 'marketplace/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('feed')
    else:
        form = LoginForm()
    return render(request, 'marketplace/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('landing')


def _open_jobs():
    return Job.objects.filter(status=Job.OPEN).select_related('employer', 'employer__profile', 'category')


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
            job.save()
            Notification.objects.create(
                user=request.user,
                title='Job posted',
                body=f'{job.title} is now visible while open.',
                url=job.get_absolute_url(),
            )
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

    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(required_skills__icontains=query))
    if category:
        jobs = jobs.filter(category_id=category)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if salary_min:
        jobs = jobs.filter(salary__gte=salary_min)
    if salary_max:
        jobs = jobs.filter(salary__lte=salary_max)
    if nearby and request.user.profile.latitude and request.user.profile.longitude:
        jobs = list(jobs)
        for job in jobs:
            if job.latitude and job.longitude:
                job.distance = round(distance_km(request.user.profile.latitude, request.user.profile.longitude, job.latitude, job.longitude), 1)
            else:
                job.distance = None
        jobs.sort(key=lambda item: item.distance if item.distance is not None else 999999)
    elif sort == 'popular':
        jobs = jobs.annotate(app_count=Count('applications')).order_by('-app_count')
    else:
        jobs = jobs.order_by('-created_at')

    return render(request, 'marketplace/find_jobs.html', {
        'jobs': jobs,
        'categories': Category.objects.all(),
        'job_types': Job.TYPE_CHOICES,
        'filters': request.GET,
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
    map_url = ''
    if job.latitude and job.longitude:
        lat = float(job.latitude)
        lng = float(job.longitude)
        map_url = (
            'https://www.openstreetmap.org/export/embed.html'
            f'?bbox={lng - 0.02}%2C{lat - 0.02}%2C{lng + 0.02}%2C{lat + 0.02}'
            f'&layer=mapnik&marker={lat}%2C{lng}'
        )
    return render(request, 'marketplace/job_detail.html', {
        'job': job,
        'comment_form': CommentForm(),
        'application_form': ApplicationForm(),
        'has_applied': Application.objects.filter(job=job, applicant=request.user).exists(),
        'is_saved': SavedJob.objects.filter(job=job, user=request.user).exists(),
        'is_liked': JobLike.objects.filter(job=job, user=request.user).exists(),
        'status_choices': Job.STATUS_CHOICES,
        'map_url': map_url,
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
    return redirect(request.POST.get('next') or 'feed')


@login_required
@require_POST
def toggle_save(request, pk):
    job = get_object_or_404(Job, pk=pk, status=Job.OPEN)
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        saved.delete()
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
    return redirect('profile_detail', username=username)


@login_required
def inbox(request):
    conversations = request.user.conversations.prefetch_related('participants', 'messages')
    active = conversations.first()
    return render(request, 'marketplace/inbox.html', {'conversations': conversations, 'active': active, 'message_form': MessageForm()})


@login_required
def start_conversation(request, username):
    other = get_object_or_404(User, username=username)
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
            'time': message.created_at.strftime('%H:%M'),
            'seen': message.seen,
        }
        for message in conversation.messages.select_related('sender')
    ]
    return JsonResponse({'messages': messages_payload})


@login_required
def notifications(request):
    notes = request.user.notifications.all()
    unread = notes.filter(read=False)
    unread.update(read=True)
    return render(request, 'marketplace/notifications.html', {'notifications': notes})


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
