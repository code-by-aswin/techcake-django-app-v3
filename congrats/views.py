from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render


def index(request):
    # Visit counter backed by the cache (Redis/ElastiCache when REDIS_URL is set).
    try:
        visits = cache.incr("techcake:visits")
    except ValueError:
        cache.set("techcake:visits", 1)
        visits = 1
    except Exception:
        visits = None  # cache unavailable; page still renders

    return render(
        request,
        "congrats/index.html",
        {"visits": visits, "version": settings.APP_VERSION},
    )


def health(request):
    """Health check for load balancers and deploy pipelines.

    200 when the app can reach its database, 503 when it can't.
    Always reports the running version so a pipeline can confirm WHICH build is live.
    """
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    return JsonResponse(
        {
            "status": "ok" if db_ok else "degraded",
            "database": "ok" if db_ok else "unreachable",
            "version": settings.APP_VERSION,
        },
        status=200 if db_ok else 503,
    )
