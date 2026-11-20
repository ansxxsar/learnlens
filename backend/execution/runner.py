"""Runs one piece of student code against one input in a throwaway container.

Security: submitted code is hostile. It never runs in the API or worker
process; each test gets a fresh Docker container that has
- no network (--network none),
- a read-only root filesystem, with small tmpfs folders for the code,
- capped memory (no swap), CPU, process count, file size and open files,
- no Linux capabilities, no privilege gain, and an unprivileged user,
- no logs on disk, and it is deleted when it stops.
The host enforces the time limit and the output limits itself, because the
student's code can tamper with anything inside its own container.

Only the worker process calls this. It needs the Docker CLI and a daemon; the
daemon must never be reachable from the API (see development.md).
"""

import base64
import logging
import os
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Bytes kept from each output stream. Anything beyond is read and dropped, so
# a program that prints forever cannot fill the worker's memory.
OUTPUT_LIMIT = 64 * 1024
# Compiling has its own budget, separate from the test's time limit.
COMPILE_TIMEOUT_S = 20
# Room for container start-up and shutdown before the host gives up.
STARTUP_TIMEOUT_S = 20
# Linux limits one environment string to 128 KiB, so the code is sent in parts.
ENV_CHUNK = 64 * 1024

DOCKER_CLIENT_VARS = ('PATH', 'HOME', 'DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_CONFIG', 'DOCKER_CERT_PATH')

# The wrapper's own exit code for a failed compile. Real programs may also use
# it, but only after the start marker, so the two cannot be confused.
COMPILE_FAILED = 200


@dataclass(frozen=True)
class Language:
    image: str
    entry_file: str
    # Shell commands run inside /work. compile may be empty.
    compile: str
    run: str
    memory_mb: int = 256
    pids: int = 64


# Images are pinned; build or pull them before starting the worker (see the
# backend README). Java gets more memory and threads because the JVM needs them.
LANGUAGES = {
    'python': Language('python:3.12-alpine', 'main.py', '', 'python3 -I main.py'),
    'javascript': Language('node:22-alpine', 'main.js', '', 'node main.js'),
    'java': Language(
        'eclipse-temurin:21-jdk-alpine',
        'Main.java',
        'javac -J-Xmx256m -J-XX:+UseSerialGC -J-XX:-UsePerfData Main.java',
        'java -Xmx256m -Xss16m -XX:+UseSerialGC -XX:-UsePerfData Main',
        memory_mb=512,
        pids=128,
    ),
    'cpp': Language(
        'learnlens-runner-cpp:1',
        'main.cpp',
        'g++ -std=c++17 -O2 -pipe -o main main.cpp',
        './main',
    ),
}

# Runs inside the container as the unprivileged user. It rebuilds the source
# from the environment, compiles it with no stdin, prints the start marker,
# then replaces itself with the program, which reads the test input.
WRAPPER = r'''
cd /work || exit 125
i=0
while :; do
  eval "part=\${SOURCE_$i-}"
  [ -n "$part" ] || break
  printf '%s' "$part"
  i=$((i + 1))
done | base64 -d > "$ENTRY_FILE" || exit 125
if [ -n "$COMPILE_CMD" ]; then
  sh -c "$COMPILE_CMD" < /dev/null > /tmp/compile.log 2>&1 || {
    head -c 16000 /tmp/compile.log >&2
    exit 200
  }
fi
printf '%s\n' "$RUN_MARKER"
exec sh -c "$RUN_CMD"
'''


class RunnerUnavailable(Exception):
    """Docker could not run the container. Not the student's fault."""


@dataclass(frozen=True)
class RunOutcome:
    stdout: str
    stderr: str
    exit_code: int | None
    compile_failed: bool = False
    # Compiling took longer than COMPILE_TIMEOUT_S; the program never ran.
    compile_timed_out: bool = False
    timed_out: bool = False
    output_truncated: bool = False
    runtime_ms: int | None = None


class _CappedReader(threading.Thread):
    """Reads a stream to the end and keeps only the first `limit` bytes.

    For stdout it also notes when the start marker arrives, which is when the
    student's program begins and its time limit starts.
    """

    def __init__(self, stream, limit, marker=None):
        super().__init__(daemon=True)
        self.stream = stream
        self.limit = limit
        self.marker = marker
        self.buffer = bytearray()
        self.truncated = False
        self.started_at = None
        # Set when the program starts, or when the stream ends without it
        # (a failed compile), so nobody waits for a start that cannot come.
        self.started_or_ended = threading.Event()

    def run(self):
        try:
            self._read()
        finally:
            self.started_or_ended.set()

    def _read(self):
        pending = bytearray() if self.marker else None
        while chunk := self.stream.read1(8192):
            if pending is not None:
                pending += chunk
                index = pending.find(self.marker)
                if index < 0:
                    # Output before the marker is the wrapper's, never shown.
                    del pending[: max(0, len(pending) - len(self.marker))]
                    continue
                self.started_at = time.monotonic()
                self.started_or_ended.set()
                chunk = bytes(pending[index + len(self.marker):])
                pending = None
            room = self.limit - len(self.buffer)
            if len(chunk) > room:
                self.truncated = True
            self.buffer += chunk[: max(room, 0)]

    def text(self):
        return self.buffer.decode('utf-8', errors='replace')


def _source_env(code):
    encoded = base64.b64encode(code.encode('utf-8')).decode('ascii')
    parts = [encoded[i: i + ENV_CHUNK] for i in range(0, len(encoded), ENV_CHUNK)] or ['']
    return {f'SOURCE_{index}': part for index, part in enumerate(parts)}


def _docker_command(name, language, env):
    memory = f'{language.memory_mb}m'
    command = [
        'docker', 'run', '--rm', '-i',
        '--name', name,
        '--network', 'none',
        '--read-only',
        '--tmpfs', '/work:rw,exec,nosuid,nodev,size=64m,mode=1777',
        '--tmpfs', '/tmp:rw,exec,nosuid,nodev,size=64m,mode=1777',
        '--memory', memory,
        '--memory-swap', memory,
        '--cpus', '1',
        '--pids-limit', str(language.pids),
        '--ulimit', 'fsize=16777216:16777216',
        '--ulimit', 'nofile=64:64',
        '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges',
        '--user', '65534:65534',
        '--log-driver', 'none',
        '--workdir', '/work',
        '--env', 'HOME=/tmp',
    ]
    # Values go through the environment of the docker CLI (--env NAME with no
    # value copies it), so the code never appears in a process list.
    for key in env:
        command += ['--env', key]
    return command + [language.image, 'sh', '-c', WRAPPER]


def _kill(name):
    # --rm removes the container once it stops.
    subprocess.run(['docker', 'kill', name], capture_output=True, timeout=30, check=False)


def run_code(language_id, code, stdin, time_limit_ms):
    """Runs `code` with `stdin` and returns what happened.

    Raises RunnerUnavailable when Docker itself fails, so the caller can mark
    the attempt as failed instead of blaming the student.
    """
    language = LANGUAGES[language_id]
    name = f'learnlens-run-{uuid.uuid4().hex}'
    marker = f'LEARNLENS-START-{uuid.uuid4().hex}'
    env = {
        **_source_env(code),
        'ENTRY_FILE': language.entry_file,
        'COMPILE_CMD': language.compile,
        'RUN_CMD': language.run,
        'RUN_MARKER': marker,
    }
    # The docker CLI gets only what it needs to find the daemon. The worker's
    # other variables, such as database passwords, are never passed on.
    process_env = {key: os.environ[key] for key in DOCKER_CLIENT_VARS if key in os.environ}
    process_env.update(env)
    try:
        process = subprocess.Popen(
            _docker_command(name, language, env),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=process_env,
        )
    except OSError as error:
        raise RunnerUnavailable(f'docker could not start: {error}') from error

    stdout = _CappedReader(process.stdout, OUTPUT_LIMIT, marker.encode() + b'\n')
    stderr = _CappedReader(process.stderr, OUTPUT_LIMIT)
    stdout.start()
    stderr.start()

    def feed_input():
        try:
            process.stdin.write(stdin.encode('utf-8'))
        except (BrokenPipeError, OSError):
            pass  # The program exited without reading all of its input.
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass

    threading.Thread(target=feed_input, daemon=True).start()

    timed_out = False
    # Phase 1: start the container and compile. Phase 2: the test itself.
    if not stdout.started_or_ended.wait(STARTUP_TIMEOUT_S + COMPILE_TIMEOUT_S):
        timed_out = True
    else:
        deadline = (stdout.started_at or time.monotonic()) + time_limit_ms / 1000
        try:
            process.wait(timeout=max(deadline - time.monotonic(), 0))
        except subprocess.TimeoutExpired:
            timed_out = True

    if timed_out:
        _kill(name)
    try:
        process.wait(timeout=STARTUP_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    finished_at = time.monotonic()
    stdout.join(5)
    stderr.join(5)

    started = stdout.started_at is not None
    exit_code = process.returncode

    if not started and not timed_out and exit_code != COMPILE_FAILED:
        # The program never began: Docker or the image failed. Its message is
        # logged for staff and never shown to students.
        logger.error('runner failed before start (exit %s): %s', exit_code, stderr.text()[:2000])
        raise RunnerUnavailable(f'container exited with {exit_code} before the program started')

    return RunOutcome(
        stdout=stdout.text(),
        stderr=stderr.text(),
        exit_code=None if timed_out else exit_code,
        compile_failed=not started and not timed_out,
        compile_timed_out=not started and timed_out,
        timed_out=timed_out and started,
        output_truncated=stdout.truncated,
        runtime_ms=round((finished_at - stdout.started_at) * 1000) if started else None,
    )
