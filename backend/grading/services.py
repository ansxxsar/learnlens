"""Approving a grade. Only an instructor's approval makes points final and
visible to the student; the suggestion alone never does (AGENTS.md)."""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from audit.models import record
from submissions.models import Submission

from .models import CriterionScore
from .scoring import suggest_points

NOT_READY = (Submission.Status.QUEUED, Submission.Status.RUNNING)


def approve_grade(submission, instructor, scores):
    """Saves the final points of every rubric criterion for this attempt.

    `scores` maps criterion id to {"points": Decimal | None, "reason": str}.
    A criterion left out, or sent without points, takes the suggestion.
    Points that differ from a suggestion need a reason, which is recorded.
    """
    if submission.status in NOT_READY:
        raise ValidationError({'detail': 'Wait until the tests have run before grading this attempt.'})

    criteria = list(submission.assignment.rubric_criteria.all())
    if not criteria:
        raise ValidationError({'detail': 'Add a rubric to this assignment before grading it.'})
    unknown = set(scores) - {criterion.id for criterion in criteria}
    if unknown:
        raise ValidationError({'scores': ['Only criteria of this assignment can be scored.']})

    suggestions = suggest_points(criteria, submission.test_results.all())
    now = timezone.now()
    rows, errors = [], {}

    for criterion in criteria:
        entry = scores.get(criterion.id, {})
        auto = suggestions[criterion.id]
        points = entry.get('points')
        reason = (entry.get('reason') or '').strip()

        if points is None:
            if auto is None:
                errors[f'score_{criterion.id}'] = f'Enter points for "{criterion.title}"; tests cannot check it.'
                continue
            points = auto
        if not Decimal(0) <= points <= criterion.max_points:
            limit = criterion.max_points
            errors[f'score_{criterion.id}'] = f'Points for "{criterion.title}" must be between 0 and {limit}.'
            continue

        overridden = auto is not None and points != auto
        if overridden and not reason:
            errors[f'score_{criterion.id}'] = f'Explain why "{criterion.title}" differs from the suggested {auto}.'
            continue

        rows.append(
            CriterionScore(
                submission=submission,
                criterion=criterion,
                auto_points=auto,
                final_points=points,
                overridden_by=instructor if overridden else None,
                override_reason=reason if overridden else None,
                overridden_at=now if overridden else None,
            )
        )

    if errors:
        # One list per criterion, in the API's usual {"field": ["message"]} shape.
        raise ValidationError({key: [message] for key, message in errors.items()})

    with transaction.atomic():
        # Approving again replaces the earlier scores; the audit log keeps both.
        submission.criterion_scores.all().delete()
        CriterionScore.objects.bulk_create(rows)
        record(
            instructor,
            'grade.approved',
            submission,
            {
                'total': str(sum((row.final_points for row in rows), Decimal(0))),
                'criteria': [
                    {
                        'criterion_id': row.criterion_id,
                        'auto': None if row.auto_points is None else str(row.auto_points),
                        'final': str(row.final_points),
                        'overridden': row.overridden_by_id is not None,
                    }
                    for row in rows
                ],
            },
        )
    return rows
