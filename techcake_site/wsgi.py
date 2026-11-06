"""WSGI config for the Techcake sample app — gunicorn's entry point."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "techcake_site.settings")

application = get_wsgi_application()
