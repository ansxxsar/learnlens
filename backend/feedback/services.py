"""Builds and stores the feedback of an attempt once its tests have run."""

import logging

from django.db import transaction

from courses.models import TestCase
from submissions.languages import LANGUAGE_BY_FILE
from submissions.models import Submission

from .models import Feedback, FeedbackItem
from .rules import EVIDENCE_VERSION, AttemptEvidence, ResultEvidence, build_feedback

logger = logging.getLogger(__name__)


def collect_evidence(submission):
    """Everything the rules may use, read from the database. Hidden tests are
    named the way students see them, so no message can reveal their names."""
    assignment = submission.assignment
    entry = submission.files.filter(is_entry_point=True).first()
    results = list(submission.test_results.select_related('test_case__criterion').order_by('test_case_id'))

    hidden_number = 0
    evidence = []
    for result in results:
        test = result.test_case
        is_hidden = test.visibility == TestCase.Visibility.HIDDEN
        if is_hidden:
            hidden_number += 1
        evidence.append(
            ResultEvidence(
                test_result_id=result.id,
                name=f'Hidden test {hidden_number}' if is_hidden else test.name,
                is_hidden=is_hidden,
                passed=result.passed,
                error_type=result.error_type,
                stdin=test.stdin_input,
                expected=test.expected_output,
                actual=result.actual_output or '',
                stderr=result.error_output or '',
                time_limit_ms=test.time_limit_ms,
                criterion_id=test.criterion_id,
                criterion_title=test.criterion.title if test.criterion else None,
            )
        )

    previous = (
        Submission.objects.filter(
            assignment=assignment,
            student=submission.student,
            attempt_number__lt=submission.attempt_number,
            status=Submission.Status.COMPLETED,
        )
        .order_by('-attempt_number')
        .first()
    )
    previous_passed = None
    if previous is not None and previous.test_results.exists():
        previous_passed = previous.test_results.filter(passed=True).count()

    untested = list(
        assignment.rubric_criteria.filter(test_cases__isnull=True).order_by('position', 'id').values_list(
            'title', flat=True
        )
    )

    return AttemptEvidence(
        language=LANGUAGE_BY_FILE.get(entry.path) if entry else '',
        depth=assignment.feedback_depth,
        results=evidence,
        attempt_number=submission.attempt_number,
        previous_passed=previous_passed,
        untested_criteria=untested,
    )


def create_rules_feedback(submission):
    """Stores rule-based feedback for the attempt, replacing any earlier one.
    Returns None when no test ran (for example, no tests or HTML)."""
    draft = build_feedback(collect_evidence(submission))
    entry = submission.files.filter(is_entry_point=True).first()

    with transaction.atomic():
        Feedback.objects.filter(submission=submission).delete()
        if draft is None:
            return None
        feedback = Feedback.objects.create(
            submission=submission,
            source=Feedback.Source.RULES,
            summary=draft.summary,
            evidence_version=EVIDENCE_VERSION,
        )
        FeedbackItem.objects.bulk_create(
            FeedbackItem(
                feedback=feedback,
                kind=item.kind,
                message=item.message,
                error_category=item.error_category,
                line_start=item.line_start,
                line_end=item.line_start,
                criterion_id=item.criterion_id,
                test_result_id=item.test_result_id,
                # A line number always refers to the student's entry file.
                file=entry if item.line_start else None,
            )
            for item in draft.items
        )
    return feedback


def safely_create_feedback(submission):
    """Feedback is extra: a bug in it must never undo the test results."""
    try:
        create_rules_feedback(submission)
    except Exception:
        logger.exception('could not build feedback for submission %s', submission.id)
