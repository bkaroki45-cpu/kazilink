from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0005_pushsubscription'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='taken_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='taken_jobs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='AttachmentPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=160)),
                ('description', models.TextField()),
                ('opportunity_type', models.CharField(choices=[('internship', 'Internship'), ('attachment', 'Attachment')], default='attachment', max_length=20)),
                ('organization', models.CharField(blank=True, max_length=160)),
                ('location', models.CharField(max_length=140)),
                ('deadline', models.DateField(blank=True, null=True)),
                ('contact_information', models.CharField(max_length=160)),
                ('required_skills', models.CharField(blank=True, max_length=255)),
                ('photo', models.ImageField(blank=True, upload_to='attachments/photos/')),
                ('document', models.FileField(blank=True, upload_to='attachments/documents/')),
                ('status', models.CharField(choices=[('open', 'Open'), ('taken', 'Taken'), ('closed', 'Closed')], default='open', max_length=20)),
                ('views', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('poster', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachment_posts', to=settings.AUTH_USER_MODEL)),
                ('taken_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='taken_attachments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='JobReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(default=5)),
                ('body', models.TextField()),
                ('positive', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='marketplace.job')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('job', 'reviewer')},
            },
        ),
        migrations.CreateModel(
            name='PasswordResetOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=6)),
                ('used', models.BooleanField(default=False)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_reset_otps', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
