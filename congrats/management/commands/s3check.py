"""
s3check — verify the app can reach its S3 bucket through the EC2 instance role.

Writes a small test object to the configured bucket and reads it back. Uses
Django's default storage (S3 via django-storages); credentials come from the
boto3 default chain, i.e. the attached IAM instance role — no access keys.

    python manage.py s3check

Exit code 0 = S3 read/write works. Non-zero = it doesn't.
"""

import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Verify S3 connectivity via the EC2 instance role (write + read a test object)."

    def handle(self, *args, **options):
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
        if not bucket:
            raise CommandError(
                "AWS_STORAGE_BUCKET_NAME is not set. Set it (and AWS_S3_REGION_NAME) "
                "in the environment before running s3check."
            )

        key = f"s3check/techcake-{uuid.uuid4().hex[:8]}.txt"
        payload = b"hello from the Techcake Django app via the EC2 instance role"

        self.stdout.write(f"Bucket: {bucket}")
        self.stdout.write(f"Writing test object: {key} ...")
        saved = default_storage.save(key, ContentFile(payload))

        self.stdout.write("Reading it back ...")
        exists = default_storage.exists(saved)
        with default_storage.open(saved) as fh:
            read_back = fh.read()

        if not (exists and read_back == payload):
            raise CommandError("S3 CHECK FAILED — wrote an object but could not read it back correctly.")

        try:
            url = default_storage.url(saved)
        except Exception:
            url = "(url unavailable)"

        self.stdout.write(self.style.SUCCESS(f"S3 CHECK PASSED — wrote and read back {len(payload)} bytes."))
        self.stdout.write(f"  object: {saved}")
        self.stdout.write(f"  url:    {url}")
        self.stdout.write("Credentials were provided by the instance role (no access keys used).")
