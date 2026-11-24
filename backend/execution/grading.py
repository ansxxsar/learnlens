"""Turns what a program did into a test verdict. Pure functions, no Docker."""

from dataclasses import dataclass

from submissions.models import TestResult

from .runner import RunOutcome

ErrorType = TestResult.ErrorType

# The program exited with SIGKILL without the host killing it: the kernel's
# out-of-memory killer, since the container has no swap.
SIGKILL_EXIT = 137

# How much of each output is stored. The runner already keeps at most 64 KiB.
STORED_OUTPUT = 16_000

COMPILE_TOO_SLOW = 'Compiling took too long and was stopped.'


@dataclass(frozen=True)
class Verdict:
    passed: bool
    error_type: str | None
    actual_output: str | None
    error_output: str | None
    runtime_ms: int | None


def normalize_output(text):
    """Outputs are compared line by line, ignoring spaces at line ends and
    blank lines at the end, so a missing final newline is not an error."""
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    lines = [line.rstrip() for line in lines]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def judge(outcome: RunOutcome, expected_output: str) -> Verdict:
    stdout = outcome.stdout[:STORED_OUTPUT]
    stderr = outcome.stderr[:STORED_OUTPUT] or None

    if outcome.compile_failed or outcome.compile_timed_out:
        message = COMPILE_TOO_SLOW if outcome.compile_timed_out else stderr
        return Verdict(False, ErrorType.COMPILE_ERROR, None, message, None)

    if outcome.timed_out:
        error_type = ErrorType.TIME_LIMIT
    elif outcome.output_truncated:
        error_type = ErrorType.OUTPUT_LIMIT
    elif outcome.exit_code == SIGKILL_EXIT:
        error_type = ErrorType.MEMORY_LIMIT
    elif outcome.exit_code != 0:
        error_type = ErrorType.RUNTIME_ERROR
    elif normalize_output(outcome.stdout) != normalize_output(expected_output):
        error_type = ErrorType.WRONG_ANSWER
    else:
        error_type = None

    return Verdict(error_type is None, error_type, stdout, stderr, outcome.runtime_ms)
