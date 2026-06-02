from django.contrib import admin

from .models import (
    ActivityUpdate, Application, AttachmentPost, Category, Comment, Conversation, Follow, Job,
    JobAlert, JobLike, JobReview, Message, Notification, PasswordResetOTP, Profile, Review, SavedJob,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'location', 'verified', 'online', 'trust_score')
    list_filter = ('role', 'verified', 'online')
    search_fields = ('user__username', 'user__email', 'location', 'skills')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'employer', 'category', 'job_type', 'status', 'taken_by', 'location', 'created_at')
    list_filter = ('status', 'job_type', 'category', 'created_at')
    search_fields = ('title', 'description', 'location', 'required_skills', 'employer__username', 'taken_by__username')
    autocomplete_fields = ('employer', 'taken_by', 'category')
    actions = ['mark_closed', 'mark_open', 'mark_taken']

    @admin.action(description='Mark selected jobs closed')
    def mark_closed(self, request, queryset):
        queryset.update(status=Job.CLOSED)

    @admin.action(description='Mark selected jobs open')
    def mark_open(self, request, queryset):
        queryset.update(status=Job.OPEN)

    @admin.action(description='Mark selected jobs taken')
    def mark_taken(self, request, queryset):
        queryset.update(status=Job.TAKEN)


@admin.register(AttachmentPost)
class AttachmentPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'poster', 'opportunity_type', 'status', 'taken_by', 'location', 'created_at')
    list_filter = ('opportunity_type', 'status', 'created_at')
    search_fields = ('title', 'description', 'organization', 'location', 'poster__username', 'taken_by__username')
    autocomplete_fields = ('poster', 'taken_by')
    actions = ['mark_closed', 'mark_open', 'mark_taken']

    @admin.action(description='Mark selected attachments closed')
    def mark_closed(self, request, queryset):
        queryset.update(status=AttachmentPost.CLOSED)

    @admin.action(description='Mark selected attachments open')
    def mark_open(self, request, queryset):
        queryset.update(status=AttachmentPost.OPEN)

    @admin.action(description='Mark selected attachments taken')
    def mark_taken(self, request, queryset):
        queryset.update(status=AttachmentPost.TAKEN)


@admin.register(JobReview)
class JobReviewAdmin(admin.ModelAdmin):
    list_display = ('job', 'reviewer', 'rating', 'positive', 'created_at')
    list_filter = ('rating', 'positive', 'created_at')
    search_fields = ('job__title', 'reviewer__username', 'reviewer__email', 'body')
    autocomplete_fields = ('job', 'reviewer')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)


admin.site.register(JobLike)
admin.site.register(SavedJob)
admin.site.register(JobAlert)
admin.site.register(Comment)
admin.site.register(Application)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(Follow)
admin.site.register(ActivityUpdate)
admin.site.register(PasswordResetOTP)
