import shutil
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import docker
from docker.errors import BuildError, DockerException

from app.models.problem import ProblemMetadata
from app.services.problem_catalog import ProblemCatalog


@dataclass
class SubmissionEvaluationResult:
    passed: bool
    logs: str
    build_time_ms: int | None = None
    image_size_bytes: int | None = None


class ProblemNotFoundError(Exception):
    pass


class DockerEvaluationError(Exception):
    pass


class DockerSubmissionService:
    def __init__(
        self,
        problems_dir: str,
        docker_socket: str = "unix:///var/run/docker.sock",
        max_build_timeout: int = 60,
        max_run_timeout: int = 30,
        submission_memory_limit: str = "256m",
        submission_cpu_quota: int = 50000,
    ) -> None:
        self.catalog = ProblemCatalog(problems_dir=problems_dir)
        self.problems_dir = Path(problems_dir)
        self.docker_socket = docker_socket
        self.max_build_timeout = max_build_timeout
        self.max_run_timeout = max_run_timeout
        self.submission_memory_limit = submission_memory_limit
        self.submission_cpu_quota = submission_cpu_quota
        self._last_build_time_ms: int | None = None
        self._last_image_size_bytes: int | None = None

    def evaluate_submission(self, problem_id: str, dockerfile_content: str) -> SubmissionEvaluationResult:
        metadata = self.catalog.get_metadata(problem_id)
        if metadata is None:
            raise ProblemNotFoundError(f"Problem '{problem_id}' not found")

        problem_dir = self.problems_dir / problem_id
        app_dir = problem_dir / "app"
        if not app_dir.is_dir():
            raise DockerEvaluationError(f"Problem '{problem_id}' is missing app/ directory")

        client = docker.DockerClient(base_url=self.docker_socket)
        self._last_build_time_ms = None
        self._last_image_size_bytes = None

        with tempfile.TemporaryDirectory(prefix=f"dockforge-{problem_id}-") as workspace_str:
            workspace = Path(workspace_str)
            self._prepare_workspace(app_dir=app_dir, workspace=workspace, dockerfile_content=dockerfile_content)

            image_tag = f"dockforge-submission:{problem_id}-{uuid4().hex[:10]}"
            build_logs = self._build_image(client=client, workspace=workspace, image_tag=image_tag)
            run_result = self._run_and_validate(client=client, metadata=metadata, image_tag=image_tag)

            combined_logs = "\n".join(
                [
                    "[build logs]",
                    build_logs.strip() or "(none)",
                    "",
                    "[runtime logs]",
                    run_result.logs.strip() or "(none)",
                ]
            )
            return SubmissionEvaluationResult(
                passed=run_result.passed,
                logs=combined_logs,
                build_time_ms=self._last_build_time_ms,
                image_size_bytes=self._last_image_size_bytes,
            )

    @staticmethod
    def _prepare_workspace(app_dir: Path, workspace: Path, dockerfile_content: str) -> None:
        for item in app_dir.iterdir():
            destination = workspace / item.name
            if item.is_dir():
                shutil.copytree(item, destination)
            else:
                shutil.copy2(item, destination)

        (workspace / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")
        (workspace / ".dockerignore").write_text(
            "\n".join(
                [
                    ".git",
                    "node_modules",
                    "__pycache__",
                    ".pytest_cache",
                    "*.pyc",
                    "solution",
                    "test.sh",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def _build_image(self, client: docker.DockerClient, workspace: Path, image_tag: str) -> str:
        build_started_at = time.monotonic()
        try:
            image, build_events = client.images.build(
                path=str(workspace),
                tag=image_tag,
                rm=True,
                forcerm=True,
                timeout=self.max_build_timeout,
            )
        except BuildError as exc:
            details = []
            for item in exc.build_log:
                if "stream" in item:
                    details.append(item["stream"].strip())
                if "error" in item:
                    details.append(item["error"].strip())
            raise DockerEvaluationError("Image build failed\n" + "\n".join(filter(None, details))) from exc
        except DockerException as exc:
            raise DockerEvaluationError(f"Docker build error: {exc}") from exc

        lines: list[str] = []
        for event in build_events:
            if "stream" in event:
                lines.append(str(event["stream"]).strip())
            if "error" in event:
                lines.append(str(event["error"]).strip())

        self._last_build_time_ms = round((time.monotonic() - build_started_at) * 1000)
        self._last_image_size_bytes = image.attrs.get("Size", 0)

        return "\n".join(filter(None, lines))

    def _run_and_validate(
        self,
        client: docker.DockerClient,
        metadata: ProblemMetadata,
        image_tag: str,
    ) -> SubmissionEvaluationResult:
        port_key = f"{metadata.app_port}/tcp"
        container = None
        try:
            container = client.containers.run(
                image=image_tag,
                detach=True,
                remove=True,
                ports={port_key: None},
                network_disabled=True,
                mem_limit=self.submission_memory_limit,
                cpu_quota=self.submission_cpu_quota,
                user="65534:65534",
            )
            container.reload()

            ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            port_info = ports.get(port_key)
            if not port_info:
                runtime_logs = self._safe_container_logs(container)
                return SubmissionEvaluationResult(
                    False,
                    f"Container did not expose port {metadata.app_port}.\n{runtime_logs}",
                    build_time_ms=self._last_build_time_ms,
                    image_size_bytes=self._last_image_size_bytes,
                )

            host_port = int(port_info[0]["HostPort"])
            health_path = metadata.health_path if metadata.health_path.startswith("/") else f"/{metadata.health_path}"
            url = f"http://127.0.0.1:{host_port}{health_path}"

            deadline = time.monotonic() + self.max_run_timeout
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen(url, timeout=2) as response:
                        if response.status == 200:
                            return SubmissionEvaluationResult(
                                True,
                                self._safe_container_logs(container),
                                build_time_ms=self._last_build_time_ms,
                                image_size_bytes=self._last_image_size_bytes,
                            )
                except urllib.error.URLError:
                    time.sleep(1)
                except TimeoutError:
                    time.sleep(1)

            runtime_logs = self._safe_container_logs(container)
            return SubmissionEvaluationResult(
                False,
                f"Health check failed at {url}\n{runtime_logs}",
                build_time_ms=self._last_build_time_ms,
                image_size_bytes=self._last_image_size_bytes,
            )
        except DockerException as exc:
            raise DockerEvaluationError(f"Docker run error: {exc}") from exc
        finally:
            if container is not None:
                try:
                    container.stop(timeout=1)
                except DockerException:
                    pass

    @staticmethod
    def _safe_container_logs(container: object) -> str:
        try:
            raw_logs = container.logs(tail=300)
            if isinstance(raw_logs, bytes):
                return raw_logs.decode("utf-8", errors="replace")
            return str(raw_logs)
        except Exception:
            return ""
