


from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def load_local_env(path):
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


load_local_env(BASE_DIR / ".env")


# ==========================
# SECURITY
# ==========================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-change-this-in-production"
)

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "testserver",
    "kazilink-dbto.onrender.com",
]


CSRF_TRUSTED_ORIGINS = [
    "https://kazilink-dbto.onrender.com",
]


# ==========================
# APPLICATIONS
# ==========================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'marketplace',
]


# ==========================
# MIDDLEWARE
# ==========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # WhiteNoise for static files on Render
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'kazilink.urls'


# ==========================
# TEMPLATES
# ==========================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates'
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'marketplace.context_processors.alert_badge',
            ],
        },
    },
]


WSGI_APPLICATION = 'kazilink.wsgi.application'


# ==========================
# DATABASE
# ==========================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ==========================
# PASSWORD VALIDATION
# ==========================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==========================
# INTERNATIONALIZATION
# ==========================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# ==========================
# STATIC FILES
# ==========================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)


# ==========================
# MEDIA FILES
# ==========================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==========================
# AUTH
# ==========================

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'feed'
LOGOUT_REDIRECT_URL = 'landing'


# ==========================
# DEFAULT PRIMARY KEY
# ==========================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==========================
# SECURITY FOR RENDER
# ==========================

SECURE_PROXY_SSL_HEADER = (
    'HTTP_X_FORWARDED_PROTO',
    'https'
)

SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False") == "True"
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "False") == "True"


# ==========================
# WEB PUSH NOTIFICATIONS
# ==========================

WEBPUSH_PUBLIC_KEY = os.environ.get("WEBPUSH_PUBLIC_KEY", "")
WEBPUSH_PRIVATE_KEY = os.environ.get("WEBPUSH_PRIVATE_KEY", "")
WEBPUSH_CLAIM_EMAIL = os.environ.get("WEBPUSH_CLAIM_EMAIL", "mailto:admin@kazisite.local")


# ==========================
# EMAIL / PASSWORD RESET OTP
# ==========================

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "in-v3.mailjet.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@kazisite.local")

