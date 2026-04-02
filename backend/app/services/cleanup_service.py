"""Background cleanup service that removes stale submission containers and images.

Runs every CLEANUP_INTERVAL_SECONDS (default 300 = 5 min) via an asyncio task
started inside FastAPI's lifespan.  Uses the Docker SDK — never subprocess.
"""

import asyncio
import logging
from datetime import datetime, timezone

import docker
from docker.errors import DockerException

logger = logging.getLogger("dockforge.cleanup")

SUBMISSION_IMAGE_PREFIX = "dockforge-submission:"
CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes
STALE_CONTAINER_THRESHOLD_SECONDS = 120  # containers older than 2 min are considered stale


def _cleanup_containers(client: docker.DockerClient) -> int:
    """Stop and remove any lingering dockforge-submission containers."""
    removed = 0
    try:
        containers = client.containers.list(all=True)
    except DockerException as exc:
        logger.warning("Failed to list containers during cleanup: %s", exc)
        return removed

    now = datetime.now(tz=timezone.utc)

    for container in containers:
        image_tags = container.image.tags if container.image else []
        is_submission = any(tag.startswith(SUBMISSION_IMAGE_PREFIX) for tag in image_tags)

        if not is_submission:
            continue

        # Check if container is old enough to be considered stale
        created_str = container.attrs.get("Created", "")
        try:
            created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            age_seconds = (now - created_at).total_seconds()
            if age_seconds < STALE_CONTAINER_THRESHOLD_SECONDS:
                continue
        except (ValueError, TypeError):
            pass  # If we can't parse the time, clean it up to be safe

        try:
            container.stop(timeout=2)
        except DockerException:
            pass

        try:
            container.remove(force=True)
            removed += 1
            logger.info("Removed stale container %s (image: %s)", container.short_id, image_tags)
        except DockerException as exc:
            logger.warning("Failed to remove container %s: %s", container.short_id, exc)

    return removed


def _cleanup_images(client: docker.DockerClient) -> int:
    """Remove dangling dockforge-submission images."""
    removed = 0
    try:
        images = client.images.list(name="dockforge-submission")
    except DockerException as exc:
        logger.warning("Failed to list images during cleanup: %s", exc)
        return removed

    for image in images:
        try:
            client.images.remove(image.id, force=True)
            removed += 1
            logger.info("Removed stale image %s (tags: %s)", image.short_id, image.tags)
        except DockerException as exc:
            logger.debug("Skipped image %s (may be in use): %s", image.short_id, exc)

    return removed


def run_cleanup(docker_socket: str) -> dict[str, int]:
    """Execute a single cleanup pass.  Returns counts of removed resources."""
    client = docker.DockerClient(base_url=docker_socket)
    containers_removed = _cleanup_containers(client)
    images_removed = _cleanup_images(client)

    if containers_removed or images_removed:
        logger.info(
            "Cleanup pass done — removed %d container(s), %d image(s)",
            containers_removed,
            images_removed,
        )
    else:
        logger.debug("Cleanup pass done — nothing to remove")

    return {"containers_removed": containers_removed, "images_removed": images_removed}


async def cleanup_loop(docker_socket: str, interval: int = CLEANUP_INTERVAL_SECONDS) -> None:
    """Async loop that calls run_cleanup every *interval* seconds."""
    docker_url = docker_socket if docker_socket.startswith("unix://") else f"unix://{docker_socket}"
    logger.info("Cleanup loop started (interval=%ds)", interval)

    while True:
        await asyncio.sleep(interval)
        try:
            await asyncio.to_thread(run_cleanup, docker_url)
        except Exception:
            logger.exception("Unexpected error in cleanup loop")
