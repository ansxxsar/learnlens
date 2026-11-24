"""Read-only queries for the instructor's gradebook.

An instructor sees the students they are responsible for: everyone in the
course when they teach it all, or only their own section.
"""

from dataclasses import dataclass, field

from django.db.models import Prefetch
from django.http import Http404

from courses.models import Assignment, Enrollment, RubricCriterion
from courses.selectors import STUDENT_VISIBLE_STATUSES
from submissions.models import Submission

from .scoring import suggest_points


def my_students(course_id, instructor):
    """Student enrollments this instructor may grade."""
    teaching = Enrollment.objects.get(user=instructor, course_id=course_id, role=Enrollment.Role.INSTRUCTOR)
    students = Enrollment.objects.filter(course_id=course_id, role=Enrollment.Role.STUDENT)
    students = students.select_related('user', 'section')
    if teaching.section_id is not None:
        students = students.filter(section_id=teaching.section_id)
    return students.order_by('user__full_name', 'user__id')


def check_can_grade(course_id, instructor, student_id):
    if not my_students(course_id, instructor).filter(user_id=student_id).exists():
        # 404, not 403: an instructor does not learn who is in other sections.
        raise Http404


def _criteria_queryset():
    return RubricCriterion.objects.order_by('position', 'id').prefetch_related('test_cases')


def _criteria_prefetch():
    return Prefetch('rubric_criteria', queryset=_criteria_queryset())


def submissions_for_review():
    return Submission.objects.select_related('student', 'assignment').prefetch_related(
        'files', 'test_results__test_case', 'criterion_scores', 'feedback__items__criterion'
    )


@dataclass
class Cell:
    latest: Submission | None = None
    graded: Submission | None = None
    # Sum of the suggested points of tested criteria. needs_review is set when
    # some criterion has no suggestion and waits for the instructor.
    suggested: object = None
    needs_review: bool = False


@dataclass
class Gradebook:
    assignments: list
    students: list
    max_points: dict = field(default_factory=dict)
    cells: dict = field(default_factory=dict)  # (assignment_id, student_id) -> Cell


def get_gradebook(course_id, instructor):
    students = list(my_students(course_id, instructor))
    assignments = list(
        Assignment.objects.filter(course_id=course_id, status__in=STUDENT_VISIBLE_STATUSES)
        .prefetch_related(_criteria_prefetch())
        .order_by('due_at', 'id')
    )
    attempts = (
        submissions_for_review()
        .filter(assignment__in=assignments, student_id__in=[student.user_id for student in students])
        .order_by('attempt_number')
    )

    book = Gradebook(assignments=assignments, students=students)
    criteria = {assignment.id: list(assignment.rubric_criteria.all()) for assignment in assignments}
    for assignment in assignments:
        book.max_points[assignment.id] = sum((criterion.max_points for criterion in criteria[assignment.id]), 0)

    for attempt in attempts:  # oldest first, so later attempts win
        cell = book.cells.setdefault((attempt.assignment_id, attempt.student_id), Cell())
        cell.latest = attempt
        if attempt.criterion_scores.all():
            cell.graded = attempt

    for (assignment_id, _), cell in book.cells.items():
        if cell.latest.status in (Submission.Status.QUEUED, Submission.Status.RUNNING):
            continue
        points = suggest_points(criteria[assignment_id], cell.latest.test_results.all())
        cell.needs_review = any(value is None for value in points.values())
        cell.suggested = sum((value for value in points.values() if value is not None), 0)
    return book


def get_attempt_for_review(course_id, assignment_id, submission_id):
    return (
        submissions_for_review()
        .prefetch_related(Prefetch('assignment__rubric_criteria', queryset=_criteria_queryset()))
        .filter(id=submission_id, assignment_id=assignment_id, assignment__course_id=course_id)
        .first()
    )
