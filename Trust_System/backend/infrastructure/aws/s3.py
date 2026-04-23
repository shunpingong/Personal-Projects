from __future__ import annotations

import logging

from infrastructure.aws.base import AbstractObjectStorage


logger = logging.getLogger(__name__)


class S3Service(AbstractObjectStorage):
    def __init__(self, region: str, default_bucket: str | None = None) -> None:
        self.region = region
        self.default_bucket = default_bucket

    async def upload_bytes(
        self,
        *,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> str:
        logger.info(
            "S3 stub upload requested",
            extra={
                "bucket": bucket,
                "key": key,
                "size_bytes": len(data),
                "content_type": content_type,
            },
        )
        return f"s3://{bucket}/{key}"

    async def delete_object(self, *, bucket: str, key: str) -> None:
        logger.info("S3 stub delete requested for %s/%s", bucket, key)

    async def get_object_url(self, *, bucket: str, key: str) -> str:
        return f"https://{bucket}.s3.{self.region}.amazonaws.com/{key}"
