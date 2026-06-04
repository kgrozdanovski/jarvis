import io
import json
import mimetypes
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse, urlunparse

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from src.core.logger import get_logger

logger = get_logger("core:storage")

APP_ENV = os.environ.get("APP_ENV", "dev")
STORAGE_HOSTNAME = os.environ.get("STORAGE_HOSTNAME", "")
STORAGE_EXTERNAL_HOSTNAME = os.environ.get("STORAGE_EXTERNAL_HOSTNAME", "")
STORAGE_PUBLIC_BUCKET = os.environ.get("STORAGE_PUBLIC_BUCKET", "")
STORAGE_PRIVATE_BUCKET = os.environ.get("STORAGE_PRIVATE_BUCKET", "")
STORAGE_KEY = os.environ.get("STORAGE_KEY", "")
STORAGE_SECRET = os.environ.get("STORAGE_SECRET", "")
STORAGE_PORT = os.environ.get("STORAGE_PORT", "")
LOCAL_STORAGE_PATH = Path(os.environ.get("LOCAL_STORAGE_PATH", "/code/storage")).resolve()
STORAGE_ALLOW_LOCAL_FALLBACK = os.environ.get(
    "STORAGE_ALLOW_LOCAL_FALLBACK",
    "true" if APP_ENV != "prod" else "false",
).lower() == "true"

_CONNECT_TIMEOUT = int(os.environ.get("STORAGE_CONNECT_TIMEOUT", "3"))
_READ_TIMEOUT = int(os.environ.get("STORAGE_READ_TIMEOUT", "5"))
_UPLOAD_RETRIES = max(0, int(os.environ.get("STORAGE_UPLOAD_RETRIES", "2")))
_FAIL_FAST = os.environ.get("STORAGE_FAIL_FAST", "true" if APP_ENV == "prod" else "false").lower() == "true"
_STARTUP_ATTEMPTS = max(1, int(os.environ.get("STORAGE_STARTUP_ATTEMPTS", "3" if APP_ENV != "prod" else "5")))
_STARTUP_RETRY_DELAY = max(0.0, float(os.environ.get("STORAGE_STARTUP_RETRY_DELAY", "1")))
_BUCKET_ALREADY_EXISTS_CODES = {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}
_MISSING_BUCKET_CODES = {"404", "NoSuchBucket", "NotFound"}

REQUIRED_SETTINGS = {
    "STORAGE_HOSTNAME": STORAGE_HOSTNAME,
    "STORAGE_PUBLIC_BUCKET": STORAGE_PUBLIC_BUCKET,
    "STORAGE_PRIVATE_BUCKET": STORAGE_PRIVATE_BUCKET,
    "STORAGE_KEY": STORAGE_KEY,
    "STORAGE_SECRET": STORAGE_SECRET,
}
missing_settings = [name for name, value in REQUIRED_SETTINGS.items() if not value]
S3_ENABLED = not missing_settings
if missing_settings:
    if STORAGE_ALLOW_LOCAL_FALLBACK:
        logger.warning(
            "Storage service missing settings (%s); S3 uploads will be skipped and local storage fallback is enabled.",
            ", ".join(sorted(missing_settings)),
        )
    else:
        logger.warning(
            "Storage service missing settings (%s); local storage fallback is disabled, so storage operations may fail.",
            ", ".join(sorted(missing_settings)),
        )


def _normalize_base_url(raw_url: str) -> str:
    """
    Ensure the provided URL has a scheme and no trailing slashes.
    """
    candidate = (raw_url or "").strip()
    if not candidate:
        return ""
    if "://" not in candidate:
        candidate = f"http://{candidate}"
    parsed = urlparse(candidate)
    cleaned = parsed._replace(path="", params="", query="", fragment="")
    return urlunparse(cleaned).rstrip("/")


def _ensure_port(base_url: str, port: str) -> str:
    """
    Attach the desired port to the base URL unless one is already present.
    """
    if not base_url:
        return ""
    if not port:
        return base_url
    parsed = urlparse(base_url)
    host = parsed.netloc or parsed.path
    if ":" in host:
        return base_url.rstrip("/")
    if parsed.netloc:
        updated = parsed._replace(netloc=f"{host}:{port}")
        return urlunparse(updated).rstrip("/")
    return f"{parsed.scheme}://{host}:{port}".rstrip("/")


STORAGE_ENDPOINT = _ensure_port(_normalize_base_url(STORAGE_HOSTNAME), STORAGE_PORT)
PUBLIC_ENDPOINT = _ensure_port(_normalize_base_url(STORAGE_EXTERNAL_HOSTNAME), STORAGE_PORT)
LOCAL_STORAGE_ENABLED = STORAGE_ALLOW_LOCAL_FALLBACK


def _bucket_name(candidate: str, access: str | None = None) -> str:
    """
    Provide a sensible fallback bucket name when configuration is missing.
    """
    if candidate:
        return candidate
    return "public" if access == "public" else "private"


def _local_bucket_path(bucket_name: str) -> Path:
    """
    Compute and ensure the directory for a bucket within the local storage root.
    """
    if not bucket_name:
        raise ValueError("Bucket name required for local storage.")
    path = LOCAL_STORAGE_PATH / bucket_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _local_object_path(bucket_name: str, object_name: str) -> Path:
    path = _local_bucket_path(bucket_name) / object_name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


class _LocalObjectBody:
    """
    Lightweight stream wrapper to mimic the boto3 response body API.
    """

    def __init__(self, path: Path, chunk_size: int = 1024 * 1024):
        self._path = path
        self._fh = path.open("rb")
        self._chunk_size = chunk_size

    def read(self, size: int | None = None) -> bytes:
        return self._fh.read(-1 if size is None else size)

    def iter_chunks(self, chunk_size: int | None = None) -> Iterable[bytes]:
        size = chunk_size or self._chunk_size
        while True:
            chunk = self._fh.read(size)
            if not chunk:
                break
            yield chunk

    def close(self) -> None:
        try:
            self._fh.close()
        except Exception:  # noqa: BLE001
            pass


def _build_local_response(bucket_name: str, object_name: str) -> dict:
    path = _local_object_path(bucket_name, object_name)
    if not path.exists():
        raise FileNotFoundError(f"Local storage object not found: {object_name}")
    mime, _ = mimetypes.guess_type(path.name)
    return {
        "Body": _LocalObjectBody(path),
        "ContentLength": path.stat().st_size,
        "ContentType": mime or "application/octet-stream",
    }


def _store_locally(file, bucket_name: str, object_name: str) -> str:
    path = _local_object_path(bucket_name, object_name)
    try:
        if isinstance(file, str):
            shutil.copyfile(file, path)
        else:
            try:
                file.seek(0)
            except Exception:  # noqa: BLE001
                pass
            with path.open("wb") as fh:
                shutil.copyfileobj(file, fh)
        logger.info("Stored %s in local storage at %s", object_name, path)
        return f"file://{path}"
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to write %s to local storage: %s", object_name, exc)
        raise


def _client_kwargs() -> dict:
    return {
        "endpoint_url": STORAGE_ENDPOINT,
        "aws_access_key_id": STORAGE_KEY,
        "aws_secret_access_key": STORAGE_SECRET,
        "config": Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=_CONNECT_TIMEOUT,
            read_timeout=_READ_TIMEOUT,
        ),
    }


def get_resource() -> boto3.resource:
    """
    Create a new S3 resource configured for the current storage endpoint.

    Warning: Resource instances are not thread safe and should not be shared across threads or processes!
    > https://boto3.amazonaws.com/v1/documentation/api/latest/guide/resources.html
    If you are using multi-threading, invoke this method in each thread.
    """
    if not S3_ENABLED:
        raise RuntimeError("S3 client requested but S3 storage is not configured.")
    return boto3.resource("s3", **_client_kwargs())


def get_client() -> boto3.client:
    """
    Create a low-level S3 client for presigned URL generation and other calls.
    """
    if not S3_ENABLED:
        raise RuntimeError("S3 client requested but S3 storage is not configured.")
    return boto3.client("s3", **_client_kwargs())


def _client_error_code(exc: ClientError) -> str:
    return str((exc.response or {}).get("Error", {}).get("Code", ""))


def _ensure_bucket_exists(client, bucket_name: str) -> None:
    """
    Ensure a configured bucket exists without requiring list-buckets permission.
    """
    try:
        client.head_bucket(Bucket=bucket_name)
        return
    except ClientError as exc:
        error_code = _client_error_code(exc)
        if error_code not in _MISSING_BUCKET_CODES:
            logger.warning("Unable to verify storage bucket '%s': %s", bucket_name, exc)
            return

    try:
        client.create_bucket(Bucket=bucket_name)
        logger.info("Created storage bucket '%s'.", bucket_name)
    except ClientError as exc:
        error_code = _client_error_code(exc)
        if error_code in _BUCKET_ALREADY_EXISTS_CODES:
            logger.info("Storage bucket '%s' already exists.", bucket_name)
            return
        logger.error("Failed to create bucket '%s': %s", bucket_name, exc)
        raise


def _ensure_public_bucket_policy(client) -> None:
    public_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicRead",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{STORAGE_PUBLIC_BUCKET}/*"],
            }
        ],
    }
    try:
        client.put_bucket_policy(Bucket=STORAGE_PUBLIC_BUCKET, Policy=json.dumps(public_policy))
    except ClientError as exc:
        logger.warning("Failed to set public policy on '%s': %s", STORAGE_PUBLIC_BUCKET, exc)


def upload_file(file, access: str, object_name: str = None) -> str:
    """
    Upload a file to an S3 bucket.

    :param file: File bytes or path to the file to upload
    :param access: Use Public/Private bucket
    :param object_name: S3 object name. If not specified then file_path is used

    :return: The URL of the uploaded file
    """
    if object_name is None:
        object_name = os.path.basename(str(uuid.uuid4()))

    bucket_name = _bucket_name(STORAGE_PUBLIC_BUCKET if access == "public" else STORAGE_PRIVATE_BUCKET, access)
    base_url = PUBLIC_ENDPOINT or STORAGE_ENDPOINT
    s3_error: Exception | None = None
    s3_uploaded = False
    file_bytes: bytes | None = None
    if not isinstance(file, str):
        try:
            file.seek(0)
        except Exception:  # noqa: BLE001
            pass
        try:
            file_bytes = file.read()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unable to snapshot upload stream for retry-safe storage writes: %s", exc)

    if S3_ENABLED:
        for attempt in range(_UPLOAD_RETRIES + 1):
            try:
                resource = get_resource()
                bucket = resource.Bucket(bucket_name)
                _ensure_bucket_exists(resource.meta.client, bucket_name)
                if isinstance(file, str):
                    bucket.upload_file(file, object_name)
                elif file_bytes is not None:
                    bucket.upload_fileobj(io.BytesIO(file_bytes), object_name)
                else:
                    try:
                        file.seek(0)
                    except Exception:  # noqa: BLE001
                        pass
                    bucket.upload_fileobj(file, object_name)
                s3_uploaded = True
                logger.info("Data uploaded to %s/%s", bucket_name, object_name)
                break
            except Exception as exc:  # noqa: BLE001
                s3_error = exc
                if attempt >= _UPLOAD_RETRIES:
                    logger.error("Failed to upload to %s/%s: %s", bucket_name, object_name, exc)
                    break
                delay_seconds = min(2.0, 0.35 * (2**attempt))
                logger.warning(
                    "Upload attempt %d/%d failed for %s/%s: %s. Retrying in %.2fs.",
                    attempt + 1,
                    _UPLOAD_RETRIES + 1,
                    bucket_name,
                    object_name,
                    exc,
                    delay_seconds,
                )
                time.sleep(delay_seconds)

    if s3_uploaded:
        return f"{base_url}/{bucket_name}/{object_name}"
    else:
        if LOCAL_STORAGE_ENABLED:
            try:
                logger.warning("Falling back to local storage for %s/%s due to S3 error.", bucket_name, object_name)

                fallback_file = io.BytesIO(file_bytes) if file_bytes is not None else file
                return _store_locally(fallback_file, bucket_name, object_name)
            except Exception as exc:  # noqa: BLE001
                if s3_error:
                    raise RuntimeError("S3 upload failed and local fallback also failed.") from exc
                raise

    if s3_error:
        raise RuntimeError(f"S3 upload failed for {bucket_name}/{object_name}.") from s3_error
    raise RuntimeError("No storage backend configured.")


def delete_file(object_name: str, access: str = "private") -> None:
    """
    Delete an object from storage. Missing objects are treated as no-op.
    """
    if not object_name:
        return

    bucket_name = _bucket_name(STORAGE_PUBLIC_BUCKET if access == "public" else STORAGE_PRIVATE_BUCKET, access)
    s3_error: Exception | None = None
    if S3_ENABLED:
        try:
            client = get_client()
            client.delete_object(Bucket=bucket_name, Key=object_name)
            logger.info("Deleted %s/%s from S3.", bucket_name, object_name)
            return
        except ClientError as exc:
            error_code = (exc.response or {}).get("Error", {}).get("Code", "")
            if error_code in {"NoSuchKey", "404"}:
                logger.info("Object %s/%s not found in S3; skipping delete.", bucket_name, object_name)
                return
            s3_error = exc
            logger.error("Failed deleting %s/%s from S3: %s", bucket_name, object_name, exc)
        except Exception as exc:  # noqa: BLE001
            s3_error = exc
            logger.error("Failed deleting %s/%s from S3: %s", bucket_name, object_name, exc)

    if LOCAL_STORAGE_ENABLED:
        try:
            local_path = (LOCAL_STORAGE_PATH / bucket_name / object_name).resolve()
            if LOCAL_STORAGE_PATH not in local_path.parents and local_path != LOCAL_STORAGE_PATH:
                raise ValueError(f"Refusing to delete path outside local storage root: {local_path}")
            if local_path.exists():
                local_path.unlink()
                logger.info("Deleted %s from local storage.", local_path)
            else:
                logger.info("Object %s missing in local storage; skipping delete.", local_path)
            return
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed deleting local object %s/%s: %s", bucket_name, object_name, exc)
            if s3_error:
                raise RuntimeError("S3 delete failed and local fallback delete also failed.") from exc
            raise

    if s3_error:
        raise RuntimeError(f"Failed deleting {bucket_name}/{object_name}.") from s3_error
    raise RuntimeError("No storage backend configured.")


def get_file(bucket_name: str, object_name: str):
    """
    Get a file from an S3 bucket.

    :param bucket_name: Name of the S3 bucket
    :param object_name: S3 object name
    :return: File object
    """
    target_bucket = _bucket_name(bucket_name)
    s3_error: Exception | None = None
    if S3_ENABLED:
        try:
            resource = get_resource()
            response = resource.Bucket(target_bucket).Object(object_name).get()
            logger.info("File %s downloaded from %s", object_name, target_bucket)
            return response
        except Exception as exc:  # noqa: BLE001
            s3_error = exc
            logger.error("Failed to download %s from %s: %s", object_name, target_bucket, exc)

    if LOCAL_STORAGE_ENABLED:
        try:
            response = _build_local_response(target_bucket, object_name)
            if s3_error:
                logger.warning(
                    "Serving %s/%s from local storage because S3 retrieval failed.", target_bucket, object_name
                )
            logger.info("File %s served from local storage bucket %s", object_name, target_bucket)
            return response
        except Exception as exc:  # noqa: BLE001
            if s3_error:
                raise s3_error
            raise

    if s3_error:
        raise s3_error
    raise RuntimeError("No storage backend configured.")


def generate_presigned_url(bucket_name: str, object_name: str, expires_in: int = 600) -> str | None:
    """
    Produce a time-limited URL for downloading an object without credentials.
    """
    if not S3_ENABLED:
        return None
    try:
        client = get_client()
        return client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expires_in,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unable to presign %s/%s: %s", bucket_name, object_name, exc)
        return None


def _ensure_default_buckets() -> None:
    """
    Create the public/private buckets when they are missing and ensure the public policy is applied.
    """
    if S3_ENABLED:
        resource = get_resource()
        client = resource.meta.client

        for bucket_name in {STORAGE_PUBLIC_BUCKET, STORAGE_PRIVATE_BUCKET}:
            _ensure_bucket_exists(client, bucket_name)

        _ensure_public_bucket_policy(client)

    for bucket_name in {
        _bucket_name(STORAGE_PUBLIC_BUCKET, "public"),
        _bucket_name(STORAGE_PRIVATE_BUCKET, "private"),
    }:
        try:
            _local_bucket_path(bucket_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unable to ensure local bucket directory for %s: %s", bucket_name, exc)


def validate_storage_on_startup() -> None:
    """
    Perform a quick connectivity check and (optionally) fail fast when storage is misconfigured.
    """
    if not S3_ENABLED:
        logger.info("S3 storage not fully configured; using local-only storage.")
        return

    if APP_ENV == "prod" and STORAGE_PORT and STORAGE_PORT not in {"443"}:
        message = (
            f"Suspicious storage port '{STORAGE_PORT}' detected in prod. "
            "Remove STORAGE_PORT or use 443 for hosted object storage."
        )
        logger.error(message)
        if _FAIL_FAST:
            raise RuntimeError(message)

    last_error: Exception | None = None
    for attempt in range(_STARTUP_ATTEMPTS):
        try:
            _ensure_default_buckets()
            logger.info("Storage connectivity check succeeded.")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= _STARTUP_ATTEMPTS - 1:
                break
            logger.warning(
                "Storage startup check attempt %d/%d failed: %s. Retrying in %.2fs.",
                attempt + 1,
                _STARTUP_ATTEMPTS,
                exc,
                _STARTUP_RETRY_DELAY,
            )
            time.sleep(_STARTUP_RETRY_DELAY)

    logger.error("Failed to initialize storage buckets: %s", last_error)
    if _FAIL_FAST and last_error:
        raise last_error
