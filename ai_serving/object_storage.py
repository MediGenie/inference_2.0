import os

from minio import Minio


MINIO_HOST = os.getenv('MINIO_HOST', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'root')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'password')
MINIO_SECURE = os.getenv('MINIO_INSECURE', 'false').lower() != 'true'
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'ais')

minio_cli = Minio(
    MINIO_HOST,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)

# Ensure that the bucket exists
if not minio_cli.bucket_exists(MINIO_BUCKET):
    minio_cli.make_bucket(MINIO_BUCKET)


def put_object(path, file):
    return minio_cli.put_object(
        MINIO_BUCKET,
        path,
        file,
        length=-1,
        part_size=100_000_000,
    )


def fput_object(path, filepath):
    return minio_cli.fput_object(
        MINIO_BUCKET,
        path,
        filepath,
        part_size=100_000_000,
    )


def get_object(path):
    return minio_cli.get_object(
        MINIO_BUCKET,
        path,
    )


def fget_object(path, filepath):
    return minio_cli.fget_object(
        MINIO_BUCKET,
        path,
        filepath,
    )
