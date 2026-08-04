from minio import Minio

from app.domain.enums import MediaBucket


def ensure_buckets(client: Minio) -> None:
    for bucket in MediaBucket:
        if not client.bucket_exists(bucket.value):
            client.make_bucket(bucket.value)
