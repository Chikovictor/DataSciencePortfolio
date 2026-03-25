import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RUNNING_DEV_SERVER = len(sys.argv) > 1 and sys.argv[1] == "runserver"


def _load_env_file(file_path):
    if not file_path.exists():
        return
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip().lstrip("\ufeff")
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_env_file(BASE_DIR / ".env")
_load_env_file(BASE_DIR / "portfolio" / ".env")


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me")
DJANGO_ENV = os.getenv("DJANGO_ENV", "production").strip().lower()
DEBUG_DEFAULT = "True" if DJANGO_ENV in {"development", "dev", "local"} else "False"
DEBUG = os.getenv("DJANGO_DEBUG", DEBUG_DEFAULT).lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,yourusername.pythonanywhere.com"
    ).split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "main.apps.MainConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
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

ROOT_URLCONF = "portfolio.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "portfolio.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Africa/Nairobi")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "main" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "portfolio-local-cache",
    }
}

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() == "true"
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "30"))
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Victor.DataScience <myportfolio332@gmail.com>",
)
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
CONTACT_FROM_NAME = os.getenv("CONTACT_FROM_NAME", "Victor.DataScience")
CONTACT_EMAIL_SUBJECT = os.getenv(
    "CONTACT_EMAIL_SUBJECT", "Inquiry via Victor's Portfolio Website"
)
CONTACT_NOTIFICATION_EMAIL = os.getenv(
    "CONTACT_NOTIFICATION_EMAIL",
    "myportfolio332@gmail.com",
)
REVIEW_NOTIFICATION_EMAIL = os.getenv(
    "REVIEW_NOTIFICATION_EMAIL",
    CONTACT_NOTIFICATION_EMAIL,
)

MAX_VISIBLE_REVIEWS = int(os.getenv("MAX_VISIBLE_REVIEWS", "10"))
CONTACT_RATE_LIMIT = int(os.getenv("CONTACT_RATE_LIMIT", "10"))
CONTACT_RATE_WINDOW_SECONDS = int(os.getenv("CONTACT_RATE_WINDOW_SECONDS", "3600"))
CONTACT_DUPLICATE_WINDOW_SECONDS = int(
    os.getenv("CONTACT_DUPLICATE_WINDOW_SECONDS", "300")
)
REVIEW_RATE_LIMIT = int(os.getenv("REVIEW_RATE_LIMIT", "5"))
REVIEW_RATE_WINDOW_SECONDS = int(os.getenv("REVIEW_RATE_WINDOW_SECONDS", "600"))
COMMENT_RATE_LIMIT = int(os.getenv("COMMENT_RATE_LIMIT", "6"))
COMMENT_RATE_WINDOW_SECONDS = int(os.getenv("COMMENT_RATE_WINDOW_SECONDS", "300"))
COMMENT_MAX_LENGTH = int(os.getenv("COMMENT_MAX_LENGTH", "1000"))
REACTION_RATE_LIMIT = int(os.getenv("REACTION_RATE_LIMIT", "30"))
REACTION_RATE_WINDOW_SECONDS = int(os.getenv("REACTION_RATE_WINDOW_SECONDS", "300"))

ADMIN_URL = os.getenv("DJANGO_ADMIN_PATH", "secure-admin/")
if not ADMIN_URL.endswith("/"):
    ADMIN_URL = f"{ADMIN_URL}/"
ADMIN_URL = ADMIN_URL.lstrip("/")

RESUME_URL = os.getenv("RESUME_URL", "/static/documents/Victor_Mwadzombo_Resume.pdf")
TIKTOK_URL = os.getenv("TIKTOK_URL", "https://www.tiktok.com/@victor.chiko")

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024

# Security profile:
# - Local dev (DEBUG=True) and local runserver stay HTTP-friendly.
# - Production enforces HTTPS + secure cookies + HSTS.
if DEBUG or RUNNING_DEV_SERVER:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
else:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")
MAIL_LOG_LEVEL = os.getenv("DJANGO_MAIL_LOG_LEVEL", "DEBUG" if DEBUG else "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
        },
        "django.core.mail": {
            "handlers": ["console"],
            "level": MAIL_LOG_LEVEL,
            "propagate": False,
        },
        "main.views": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
