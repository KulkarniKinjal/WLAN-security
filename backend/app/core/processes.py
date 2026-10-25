from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable


@dataclass
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    interrupted: bool
    reason: str = ""


def terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    process.terminate()


def run_process(
    args: list[str],
    timeout: float,
    check_cancelled: Callable[[], bool],
    register: Callable[[subprocess.Popen[str]], None],
    unregister: Callable[[subprocess.Popen[str]], None],
    max_log_chars: int = 4000,
) -> ProcessResult:
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    kwargs: dict = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "bufsize": 1,
        "creationflags": creationflags,
    }
    if os.name == "posix":
        kwargs["start_new_session"] = True

    process = subprocess.Popen(args, **kwargs)
    register(process)
    stdout_tail: deque[str] = deque()
    stderr_tail: deque[str] = deque()
    output_lock = threading.Lock()

    def drain(stream, target: deque[str]) -> None:
        for line in iter(stream.readline, ""):
            with output_lock:
                target.append(line)
                while sum(len(item) for item in target) > max_log_chars:
                    target.popleft()
        stream.close()

    stdout_thread = threading.Thread(target=drain, args=(process.stdout, stdout_tail), daemon=True)
    stderr_thread = threading.Thread(target=drain, args=(process.stderr, stderr_tail), daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    started = time.monotonic()
    interrupted = False
    reason = ""
    try:
        while process.poll() is None:
            if check_cancelled():
                interrupted, reason = True, "cancelled"
                terminate_process_group(process)
                break
            if time.monotonic() - started > timeout:
                interrupted, reason = True, "timed out"
                terminate_process_group(process)
                break
            time.sleep(0.05)
        if process.poll() is None:
            process.wait(timeout=2)
        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)
        return ProcessResult(
            process.returncode if process.returncode is not None else -1,
            "".join(stdout_tail),
            "".join(stderr_tail),
            interrupted,
            reason,
        )
    finally:
        unregister(process)
