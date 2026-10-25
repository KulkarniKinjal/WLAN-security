import sys

from app.core.processes import run_process


def test_process_runner_drains_large_output_without_deadlock():
    result = run_process(
        [sys.executable, "-c", "print('x' * 1000000)"],
        timeout=5,
        check_cancelled=lambda: False,
        register=lambda process: None,
        unregister=lambda process: None,
    )
    assert result.interrupted is False
    assert result.returncode == 0
    assert len(result.stdout) <= 4000
