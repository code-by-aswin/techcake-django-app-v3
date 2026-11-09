FROM python:3.10.11-slim-buster
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ARG APP_VERSION=unknown
ENV APP_VERSION=$APP_VERSION
EXPOSE 8000
CMD ["gunicorn", "techcake_site.wsgi:application", "--bind", "0.0.0.0:8000"]