"""Runs a queued attempt against its assignment's tests and stores results.

Called only by the Celery worker (execution/tasks.py), never by the API.
"""

import logging

from django.db import transaction

from feedback.services import safely_create_feedback
from submissions.languages import LANGUAGE_BY_FILE
from submissions.models import Submission, TestResult

from .grading import judge
from .runner import LANGUAGES, RunnerUnavailable, run_code

logger = logging.getLogger(__name__)

Status = Submission.Status


def _claim(submission_id):
    """Moves the attempt from queued to running. Returns False when another
    worker already took it, or it no longer exists."""
    return bool(Submission.objects.filter(id=submission_id, status=Status.QUEUED).update(status=Status.RUNNING))


def execute_submission(submission_id):
    if not _claim(submission_id):
        logger.info('submission %s is not queued; skipped', submission_id)
        return

    submission = Submission.objects.select_related('assignment').get(id=submission_id)
    entry = submission.files.filter(is_entry_point=True).first()
    language = LANGUAGE_BY_FILE.get(entry.path) if entry else None

    if language not in LANGUAGES:
        # HTML and CSS are not run; there is nothing to execute yet.
        submission.status = Status.COMPLETED
        submission.save(update_fields=['status'])
        return

    tests = list(submission.assignment.test_cases.order_by('id'))
    try:
        verdicts = []
        for test in tests:
            outcome = run_code(language, entry.content, test.stdin_input, test.time_limit_ms)
            verdicts.append((test, judge(outcome, test.expected_output)))
    except RunnerUnavailable:
        # Logged without the student's code. The attempt can be queued again
        # once the runner works (manage.py requeue_submissions).
        logger.exception('runner unavailable for submission %s', submission_id)
        submission.status = Status.FAILED
        submission.save(update_fields=['status'])
        return

    with transaction.atomic():
        # A rerun replaces earlier results instead of adding to them.
        submission.test_results.all().delete()
        TestResult.objects.bulk_create(
            TestResult(
                submission=submission,
                test_case=test,
                passed=verdict.passed,
                actual_output=verdict.actual_output,
                error_output=verdict.error_output,
                error_type=verdict.error_type,
                runtime_ms=verdict.runtime_ms,
            )
            for test, verdict in verdicts
        )
        submission.status = Status.COMPLETED
        submission.save(update_fields=['status'])

    safely_create_feedback(submission)
