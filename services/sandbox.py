"""Disposable Docker workspaces; no host mounts, credentials, or target commands on host."""
from __future__ import annotations
import io
import json
import os
import subprocess
import tarfile
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

MAX_SOURCE_BYTES = 128 * 1024 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
EXCLUDED = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}

class SandboxError(RuntimeError):
    pass

@dataclass
class RunResult:
    exit_code: int
    stdout: str
    output: bytes | None
    image: str
    duration: float


def docker(args: list[str], *, timeout: int = 60, data: bytes | None = None,
           check: bool = True) -> subprocess.CompletedProcess:
    # Spool CLI output to disk, then enforce a cap rather than unbounded PIPE memory.
    with tempfile.TemporaryFile() as output:
        try:
            result = subprocess.run(["docker", *args], input=data, stdout=output,
                                    stderr=subprocess.STDOUT, timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise SandboxError("Docker unavailable or command timed out") from error
        size = output.tell()
        if size > MAX_OUTPUT_BYTES:
            raise SandboxError("Worker output exceeded size limit")
        output.seek(0)
        result.stdout = output.read()
    if check and result.returncode:
        # Docker diagnostics can contain target-controlled text; retain a bounded tail.
        detail = result.stdout.decode("utf-8", "replace")[-1200:]
        raise SandboxError(f"Docker command failed ({result.returncode}): {detail}")
    return result


def source_archive(root: Path, extra: dict[str, bytes] | None = None) -> bytes:
    root = root.resolve()
    buffer = io.BytesIO()
    total = 0
    count = 0
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name in ("src", "out"):
            entry = tarfile.TarInfo(name)
            entry.type = tarfile.DIRTYPE
            entry.mode = 0o777
            entry.uid = entry.gid = 1000
            archive.addfile(entry)
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root)
            if any(part in EXCLUDED for part in rel.parts):
                continue
            if path.is_symlink():
                raise SandboxError("Repository symlinks are not supported")
            if not path.is_file():
                continue
            size = path.stat().st_size
            total += size
            count += 1
            if total > MAX_SOURCE_BYTES or size > 8 * 1024 * 1024 or count > 20000:
                raise SandboxError("Repository exceeds the bounded worker input size")
            entry = tarfile.TarInfo("src/" + rel.as_posix())
            entry.size, entry.mode = size, 0o644
            entry.uid = entry.gid = 1000
            with path.open("rb") as content:
                archive.addfile(entry, content)
        for name, data in (extra or {}).items():
            if "/" in name or "\\" in name or name in {".", ".."}:
                raise SandboxError("Invalid worker input name")
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode = len(data), 0o644
            entry.uid = entry.gid = 1000
            archive.addfile(entry, io.BytesIO(data))
    return buffer.getvalue()


def run_container(image: str, command: list[str], root: Path, *,
                  output_file: str | None = None, extra: dict[str, bytes] | None = None,
                  network: bool = False, timeout: int = 600, memory: str = "2g",
                  prepare_command: list[str] | None = None) -> RunResult:
    started = time.monotonic()
    identity = "traceguard-" + uuid.uuid4().hex
    volume = identity + "-data"
    image_info = docker(["image", "inspect", image, "--format", "{{.Id}}"], check=False)
    if image_info.returncode:
        if image.startswith(("traceguard/", "sha256:")):
            raise SandboxError("Required local worker image unavailable; run scripts/setup-workers.ps1: " + image)
        docker(["pull", image], timeout=600)
        image_info = docker(["image", "inspect", image, "--format", "{{.Id}}"])
    image_id = image_info.stdout.decode().strip()
    archive = source_archive(root, extra)
    docker(["volume", "create", "--label", "traceguard.worker=true", volume])
    try:
        create_args = ["create", "--name", identity, "--label", "traceguard.worker=true",
                "--network", "bridge" if network else "none", "--read-only",
                "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
                "--pids-limit=256", "--memory=" + memory, "--memory-swap=" + memory,
                "--cpus=2", "--user=1000:1000", "--init",
                "--ulimit", "fsize=2147483648:2147483648",
                "--log-driver=local", "--log-opt=max-size=10m", "--log-opt=max-file=2",
                "--tmpfs", "/tmp:rw,exec,nosuid,size=1073741824,mode=1777",
                "--mount", f"type=volume,source={volume},target=/workspace",
                "--workdir", "/workspace/src", "--env", "HOME=/tmp",
                "--env", "PYTHONDONTWRITEBYTECODE=1",
                "--env", "JAVA_OPTS=-Duser.home=/tmp -Xmx3g",
                "--entrypoint", command[0], image_id, *command[1:]]
        if prepare_command:
            prep_args = create_args[:]
            prep_args[prep_args.index("--network") + 1] = "bridge"
            entry_index = prep_args.index("--entrypoint")
            prep_args[entry_index:] = ["--entrypoint", prepare_command[0], image_id, *prepare_command[1:]]
            docker(prep_args)
            docker(["cp", "-", identity + ":/workspace"], data=archive)
            docker(["start", "--attach", identity], timeout=timeout, check=False)
            state = json.loads(docker(["inspect", identity, "--format", "{{json .State}}"] ).stdout)
            if state["ExitCode"] != 0 or state.get("OOMKilled"):
                raise SandboxError("Dependency preparation failed (lifecycle scripts disabled); check lockfile and registry availability")
            docker(["rm", identity])
        docker(create_args)
        if not prepare_command:
            docker(["cp", "-", identity + ":/workspace"], data=archive)
        result = docker(["start", "--attach", identity], timeout=timeout, check=False)
        state = json.loads(docker(["inspect", identity, "--format", "{{json .State}}"] ).stdout)
        if state.get("OOMKilled"):
            raise SandboxError("Worker exceeded its memory limit")
        report = None
        if output_file:
            if not output_file.startswith("/workspace/out/") or ".." in output_file:
                raise SandboxError("Invalid output path")
            copied = docker(["cp", identity + ":" + output_file, "-"], check=False)
            if copied.returncode == 0:
                with tarfile.open(fileobj=io.BytesIO(copied.stdout)) as content:
                    members = content.getmembers()
                    if len(members) != 1 or not members[0].isfile() or members[0].size > MAX_OUTPUT_BYTES:
                        raise SandboxError("Invalid worker output artifact")
                    report = content.extractfile(members[0]).read()
        return RunResult(state["ExitCode"], result.stdout.decode("utf-8", "replace"),
                         report, image_id, round(time.monotonic() - started, 2))
    finally:
        # Names are generated here; never remove unrelated user containers or volumes.
        docker(["rm", "--force", identity], check=False)
        docker(["volume", "rm", "--force", volume], check=False)
