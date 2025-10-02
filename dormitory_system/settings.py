from pathlib import Path
import os
import environ
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# โหลดค่า .env
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
load_dotenv()

# Security
SECRET_KEY = env("SECRET_KEY", default="django-insecure-xxxx")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Application definition
INSTALLED_APPS = [
    # core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # third-party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    # local apps
    "dorms",
    "rooms",
    "accounts",
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # ✅ ต้องมี
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "dormitory_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # ✅ โฟลเดอร์ template หลัก
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # ✅ ต้องมีสำหรับ allauth
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "dormitory_system.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "th"
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
USE_TZ = True

# Static & Media
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DEFAULT_DOMAIN = "127.0.0.1:8000"   # สำหรับ development
DEFAULT_PROTOCOL = "http"   

# Login / Logout
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dorms/"
LOGOUT_REDIRECT_URL = "/login/"

# Email config (ใช้ Gmail SMTP + App Password)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="pansak.pa.66@ubu.ac.th")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="pylc shet djgq rjzu")  # ใช้ App Password ของ Gmail
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Django Allauth settings
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"  # ✅ ใช้ "mandatory" ถ้า production
ACCOUNT_USERNAME_REQUIRED = True

ACCOUNT_LOGIN_REDIRECT_URL = "/dorms/"
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True
ACCOUNT_LOGOUT_REDIRECT_URL = "/login/"

# Social login (Google OAuth2)
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"prompt": "select_account"},
        "APP": {
            "client_id": env("GOOGLE_CLIENT_ID"),
            "secret": env("GOOGLE_CLIENT_SECRET"),
            "key": "",
        },
    }
}
