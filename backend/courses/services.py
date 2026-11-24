"""Assignment rules for instructors. Views call these instead of changing
models directly, so the rules live in one place."""

from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from .models import Assignment, RubricCriterion, TestCase


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


def ensure_editable(assignment):
    """Archived work is frozen, together with its rubric and tests."""
    if assignment.status == Status.ARCHIVED:
        raise AssignmentRuleError('Archived assignments cannot be changed.')


def update_assignment(assignment, *, status=None, **fields):
    ensure_editable(assignment)

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


# Rubric criteria and test cases. Both belong to one assignment; the views
# look them up inside the URL's course and assignment before calling these.


def _set_fields(instance, fields):
    for name, value in fields.items():
        setattr(instance, name, value)
    instance.save()
    return instance


def create_criterion(assignment, **fields):
    ensure_editable(assignment)
    if 'position' not in fields:
        # New criteria go to the end of the rubric.
        last = assignment.rubric_criteria.aggregate(last=Max('position'))['last']
        fields['position'] = 0 if last is None else last + 1
    return RubricCriterion.objects.create(assignment=assignment, **fields)


def update_criterion(criterion, **fields):
    ensure_editable(criterion.assignment)
    return _set_fields(criterion, fields)


def delete_criterion(criterion):
    # Its test cases stay and are only unlinked (on_delete=SET_NULL).
    ensure_editable(criterion.assignment)
    criterion.delete()


def _check_criterion(assignment, fields):
    """A test may only count toward a criterion of its own assignment. The
    serializer sends `criterion` as an id; it is stored as criterion_id."""
    if 'criterion' not in fields:
        return
    criterion_id = fields.pop('criterion')
    if criterion_id is not None and not assignment.rubric_criteria.filter(id=criterion_id).exists():
        raise ValidationError({'criterion': ["Choose a criterion from this assignment's rubric."]})
    fields['criterion_id'] = criterion_id


def create_test_case(assignment, **fields):
    ensure_editable(assignment)
    _check_criterion(assignment, fields)
    return TestCase.objects.create(assignment=assignment, **fields)


def update_test_case(test_case, **fields):
    ensure_editable(test_case.assignment)
    _check_criterion(test_case.assignment, fields)
    return _set_fields(test_case, fields)


def delete_test_case(test_case):
    ensure_editable(test_case.assignment)
    test_case.delete()
