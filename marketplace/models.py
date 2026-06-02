from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from pathlib import PurePath


class Profile(models.Model):
    EMPLOYER = 'employer'
    SEEKER = 'seeker'
    ROLE_CHOICES = (
        (EMPLOYER, 'Employer'),
        (SEEKER, 'Job Seeker'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    bio = models.TextField(blank=True)
    skills = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=120, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    avatar = models.ImageField(upload_to='profiles/avatars/', blank=True)
    cover_photo = models.ImageField(upload_to='profiles/covers/', blank=True)
    verified = models.BooleanField(default=False)
    online = models.BooleanField(default=False)
    trust_score = models.PositiveIntegerField(default=80)
    resume = models.FileField(upload_to='profiles/resumes/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} profile'

    @property
    def rating_average(self):
        aggregate = self.user.received_reviews.aggregate(models.Avg('rating'))
        return round(aggregate['rating__avg'] or 0, 1)


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    icon = models.CharField(max_length=40, default='briefcase')

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Job(models.Model):
    IMMEDIATE = 'immediate'
    SHORT_TERM = 'short_term'
    LONG_TERM = 'long_term'
    PART_TIME = 'part_time'
    FULL_TIME = 'full_time'
    CASUAL = 'casual'
    FREELANCE = 'freelance'
    PROFESSIONAL = 'professional'
    TYPE_CHOICES = (
        (IMMEDIATE, 'Immediate'),
        (SHORT_TERM, 'Short-term'),
        (LONG_TERM, 'Long-term'),
        (PART_TIME, 'Part-time'),
        (FULL_TIME, 'Full-time'),
        (CASUAL, 'Casual'),
        (FREELANCE, 'Freelance'),
        (PROFESSIONAL, 'Professional'),
    )
    OPEN = 'open'
    TAKEN = 'taken'
    CLOSED = 'closed'
    STATUS_CHOICES = (
        (OPEN, 'Open'),
        (TAKEN, 'Taken'),
        (CLOSED, 'Closed'),
    )

    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=160)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='jobs')
    job_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=140)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    resolved_place_name = models.CharField(max_length=255, blank=True)
    deadline = models.DateField(null=True, blank=True)
    required_skills = models.CharField(max_length=255, blank=True)
    contact_information = models.CharField(max_length=160)
    photo = models.ImageField(upload_to='jobs/photos/', blank=True)
    video = models.FileField(upload_to='jobs/videos/', blank=True)
    audio = models.FileField(upload_to='jobs/audio/', blank=True)
    document = models.FileField(upload_to='jobs/documents/', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)
    taken_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='taken_jobs')
    tags = models.CharField(max_length=200, blank=True)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('job_detail', kwargs={'pk': self.pk})

    @property
    def is_visible(self):
        return self.status == self.OPEN

    @property
    def is_taken(self):
        return self.status == self.TAKEN


class AttachmentPost(models.Model):
    INTERNSHIP = 'internship'
    ATTACHMENT = 'attachment'
    TYPE_CHOICES = (
        (INTERNSHIP, 'Internship'),
        (ATTACHMENT, 'Attachment'),
    )
    OPEN = 'open'
    TAKEN = 'taken'
    CLOSED = 'closed'
    STATUS_CHOICES = (
        (OPEN, 'Open'),
        (TAKEN, 'Taken'),
        (CLOSED, 'Closed'),
    )

    poster = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attachment_posts')
    title = models.CharField(max_length=160)
    description = models.TextField()
    opportunity_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=ATTACHMENT)
    organization = models.CharField(max_length=160, blank=True)
    location = models.CharField(max_length=140)
    deadline = models.DateField(null=True, blank=True)
    contact_information = models.CharField(max_length=160)
    required_skills = models.CharField(max_length=255, blank=True)
    photo = models.ImageField(upload_to='attachments/photos/', blank=True)
    document = models.FileField(upload_to='attachments/documents/', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)
    taken_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='taken_attachments')
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('attachment_detail', kwargs={'pk': self.pk})

    @property
    def is_taken(self):
        return self.status == self.TAKEN


class JobLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_likes')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saves')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')


class JobAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_alerts')
    keyword = models.CharField(max_length=160, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_alerts')
    job_type = models.CharField(max_length=30, choices=Job.TYPE_CHOICES, blank=True)
    location = models.CharField(max_length=160, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_km = models.PositiveIntegerField(default=20)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} alert'


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField(max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class JobReview(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    body = models.TextField()
    positive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('job', 'reviewer')

    def __str__(self):
        return f'{self.reviewer.username} review for {self.job}'


class Application(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
    )

    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('applicant', 'job')


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-updated_at']


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    hidden_for = models.ManyToManyField(User, blank=True, related_name='hidden_messages')
    body = models.TextField(blank=True)
    attachment = models.FileField(upload_to='chat/files/', blank=True)
    image = models.ImageField(upload_to='chat/images/', blank=True)
    voice_note = models.FileField(upload_to='chat/voice/', blank=True)
    seen = models.BooleanField(default=False)
    deleted_for_everyone = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    @property
    def attachment_name(self):
        if not self.attachment:
            return ''
        return PurePath(self.attachment.name).name

    @property
    def attachment_kind(self):
        if not self.attachment:
            return ''
        suffix = PurePath(self.attachment.name).suffix.lower().lstrip('.')
        if suffix in {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'avif'}:
            return 'image'
        if suffix in {'mp4', 'webm', 'mov', 'm4v', 'avi', 'mkv'}:
            return 'video'
        if suffix in {'mp3', 'wav', 'ogg', 'm4a', 'aac', 'flac'}:
            return 'audio'
        if suffix == 'pdf':
            return 'pdf'
        if suffix in {'doc', 'docx', 'txt', 'rtf', 'odt'}:
            return 'document'
        if suffix in {'xls', 'xlsx', 'csv'}:
            return 'spreadsheet'
        if suffix in {'ppt', 'pptx'}:
            return 'presentation'
        return 'file'


class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='written_reviews')
    reviewed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    body = models.TextField()
    positive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('reviewer', 'reviewed')


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=240, blank=True)
    url = models.CharField(max_length=240, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_otps')
    code = models.CharField(max_length=6)
    used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self, code):
        return not self.used and self.code == code and self.expires_at >= timezone.now()


class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=600, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')


class ActivityUpdate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updates')
    body = models.TextField()
    media = models.FileField(upload_to='updates/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
