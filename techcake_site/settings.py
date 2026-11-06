"""
Django settings for the Techcake sample app — v3 (CI/CD-ready).

v2 adds Amazon S3 media storage (via django-storages / boto3). AWS credentials
are NOT configured here: boto3 uses the default credential chain, which on EC2
resolves to the attached IAM **instance role**. Never put access keys in this app.

All environment-specific values are read from environment variables. See README.md.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security -------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

# --- Applications ---------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "congrats",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "techcake_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "techcake_site.wsgi.application"

# --- Database -------------------------------------------------------
# Production: MySQL/MariaDB (Amazon RDS). For running the test suite (locally or
# in CI) set DB_ENGINE=sqlite — no database server needed.
if os.environ.get("DB_ENGINE", "mysql").lower() == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "django1"),
            "USER": os.environ.get("DB_USER", "django1_user"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),  # your RDS endpoint
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }

# --- Release version -------------------------------------------------
# Set by your pipeline (e.g. the git commit SHA) so the running app can prove
# exactly which build it is. Shown on the home page and returned by /health.
APP_VERSION = os.environ.get("APP_VERSION", "v3-dev")

# --- Passwords ------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18N / TZ ------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static & media -------------------------------------------------
# Static files stay local (collectstatic). Media (uploads) go to S3.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# S3 media storage via django-storages. Credentials come from the EC2
# instance role (the default boto3 chain) — NOT from keys.
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None          # rely on the bucket's own policy/ownership
AWS_QUERYSTRING_AUTH = True     # serve private objects via signed URLs

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MEDIA_URL = "/media/"

# --- Cache (Redis) --------------------------------------------------
# When REDIS_URL is set (e.g. redis://redis:6379/0 in the Compose stack)
# the app uses Redis; otherwise it falls back to a local in-memory cache so
# it still runs without Redis. The visit counter on the home page uses this.
REDIS_URL = os.environ.get("REDIS_URL", "")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
