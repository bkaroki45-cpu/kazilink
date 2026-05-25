from django.contrib import admin

from .models import (
    ActivityUpdate, Application, Category, Comment, Conversation, Follow, Job,
    JobLike, Message, Notification, Profile, Review, SavedJob,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'location', 'verified', 'online', 'trust_score')
    list_filter = ('role', 'verified', 'online')
    search_fields = ('user__username', 'user__email', 'location', 'skills')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'employer', 'category', 'job_type', 'status', 'location', 'created_at')
    list_filter = ('status', 'job_type', 'category', 'created_at')
    search_fields = ('title', 'description', 'location', 'required_skills')
    actions = ['mark_closed', 'mark_open']

    @admin.action(description='Mark selected jobs closed')
    def mark_closed(self, request, queryset):
        queryset.update(status=Job.CLOSED)

    @admin.action(description='Mark selected jobs open')
    def mark_open(self, request, queryset):
        queryset.update(status=Job.OPEN)


admin.site.register(Category)
admin.site.register(JobLike)
admin.site.register(SavedJob)
admin.site.register(Comment)
admin.site.register(Application)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(Follow)
admin.site.register(ActivityUpdate)
