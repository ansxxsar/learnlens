"""Rules for storing a student's attempt.

Security: the code is saved as text and nothing here runs it. Running
submissions is the job of the isolated execution workers (execution/), which
pick up attempts in the "queued" status.
"""

from django.db import IntegrityError, transaction
from django.db.models import Max
from rest_framework.exceptions import APIException

from courses.models import Assignment
from execution.tasks import enqueue_submission

from .languages import ENTRY_FILES
from .models import Submission, SubmissionFile


class SubmissionRuleError(APIException):
    """A 400 answered as {"detail": "..."}."""

    status_code = 400


class SubmissionConflict(APIException):
    status_code = 409
    default_detail = 'Another attempt was saved at the same moment. Please submit again.'


def create_submission(assignment, student, language, code):
    # Closed assignments keep their history but take no new attempts. Drafts
    # and archived ones are already hidden from students (404 in the view).
    if assignment.status != Assignment.Status.PUBLISHED:
        raise SubmissionRuleError('This assignment is closed and no longer accepts attempts.')

    try:
        with transaction.atomic():
            last = Submission.objects.filter(assignment=assignment, student=student).aggregate(
                last=Max('attempt_number')
            )['last']
            submission = Submission.objects.create(
                assignment=assignment, student=student, attempt_number=(last or 0) + 1
            )
            SubmissionFile.objects.create(
                submission=submission, path=ENTRY_FILES[language], content=code, is_entry_point=True
            )
    except IntegrityError:
        # Two requests counted the same attempt number; the unique key let
        # only one through.
        raise SubmissionConflict()
    # Only after the attempt is saved, so the worker can always find it.
    transaction.on_commit(lambda: enqueue_submission(submission.id))
    return submission
