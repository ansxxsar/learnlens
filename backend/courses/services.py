"""Assignment rules for instructors. Views call these instead of changing
models directly, so the rules live in one place."""

from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from .models import Assignment


class AssignmentRuleError(APIException):
    """A 400 answered as {"detail": "..."}, the shape the frontend shows as a
    page message. ValidationError would wrap the message in a list."""

    status_code = 400


Status = Assignment.Status

# Which status an assignment may move to from its current one. Archived is
# final; a closed assignment may be reopened.
ALLOWED_TRANSITIONS = {
    Status.DRAFT: {Status.PUBLISHED},
    Status.PUBLISHED: {Status.CLOSED, Status.ARCHIVED},
    Status.CLOSED: {Status.PUBLISHED, Status.ARCHIVED},
    Status.ARCHIVED: set(),
}


def _publish(assignment):
    assignment.status = Status.PUBLISHED
    # Keep the first publish time when a closed assignment is reopened.
    if assignment.published_at is None:
        assignment.published_at = timezone.now()


def create_assignment(course_id, *, publish=False, **fields):
    assignment = Assignment(course_id=course_id, **fields)
    if publish:
        _publish(assignment)
    assignment.save()
    return assignment


def update_assignment(assignment, *, status=None, **fields):
    if assignment.status == Status.ARCHIVED:
        raise AssignmentRuleError('Archived assignments cannot be changed.')

    for name, value in fields.items():
        setattr(assignment, name, value)

    if status is not None and status != assignment.status:
        if status not in ALLOWED_TRANSITIONS[assignment.status]:
            raise ValidationError({'status': [f'A {assignment.status} assignment cannot become {status}.']})
        if status == Status.PUBLISHED:
            _publish(assignment)
        else:
            assignment.status = status

    assignment.save()
    return assignment


def delete_assignment(assignment):
    # Published work may already have student attempts, so it is archived
    # instead of deleted.
    if assignment.status != Status.DRAFT:
        raise AssignmentRuleError('Only draft assignments can be deleted. Archive it instead.')
    assignment.delete()
