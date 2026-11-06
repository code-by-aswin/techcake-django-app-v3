# Techcake Sample Django App — v3 (CI/CD-ready)

The Track 3 version of the Techcake app. Everything v2 had (Amazon RDS, S3 via the
EC2 instance role, Redis/ElastiCache visit counter, `s3check`) **plus** what a
pipeline needs:

- **A test suite** — `congrats/tests.py`. Your pipeline must run it and stop if it fails.
- **A health endpoint** — `GET /health` returns `200` when the app can reach its
  database and `503` when it can't, and always reports the running version.
- **A version label** — set `APP_VERSION` (your pipeline should use the git commit SHA).
  It's shown on the home page and returned by `/health`, so you can prove which build is live.

> Your task is to build the pipeline around this app — not to rewrite it.

## Run the tests (no database server needed)

```
pip install -r requirements.txt
DB_ENGINE=sqlite python manage.py test
```

## Environment variables

Everything from v2, plus:

| Variable | Purpose | Example |
|---|---|---|
| `APP_VERSION` | release label shown on the page and in `/health` | the git commit SHA |
| `DB_ENGINE` | set to `sqlite` to run tests without MySQL; leave unset in production | `sqlite` |

v2 variables (unchanged): `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`,
`DJANGO_CSRF_TRUSTED_ORIGINS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`,
`AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `REDIS_URL`.

AWS credentials are never configured in the app — they come from the instance role.

## Health check

```
curl -s https://djangov2.<studentid>.nixlabs.in/health
{"status": "ok", "database": "ok", "version": "3f9c2ab..."}
```

Refer to your Track 3 task sheet for the requirements and definition of done.
