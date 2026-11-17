"""Read-only course queries used by the API.

Every query starts from the signed-in user's own enrollments, so a user can
only ever see courses they belong to.
"""

from dataclasses import dataclass

from .models import Assignment, Enrollment


@dataclass(frozen=True)
class MyCourse:
    enrollment: Enrollment
    instructor_names: list[str]
    # Only filled for instructors. Students are not told how many classmates
    # they have, because they do not need it.
    student_count: int | None


def _teaches(instructor, enrollment):
    """An instructor without a section teaches the whole course. One with a
    section teaches only that section."""
    return instructor.section_id is None or instructor.section_id == enrollment.section_id


def _counts_toward(student, enrollment):
    """The students an instructor is responsible for: their own section, or
    every student when they teach the whole course."""
    return enrollment.section_id is None or student.section_id == enrollment.section_id


def get_my_courses(user, course_id=None):
    """All of the user's courses, or only `course_id` when it is given."""
    enrollments = user.enrollments.select_related('course', 'section').order_by('course__code', 'course__id')
    if course_id is not None:
        enrollments = enrollments.filter(course_id=course_id)
    enrollments = list(enrollments)
    course_ids = [enrollment.course_id for enrollment in enrollments]

    # Two queries for all courses together, instead of two per course.
    instructors = list(
        Enrollment.objects.filter(course_id__in=course_ids, role=Enrollment.Role.INSTRUCTOR)
        .select_related('user')
        .order_by('user__full_name', 'user__id')
    )
    students = list(
        Enrollment.objects.filter(course_id__in=course_ids, role=Enrollment.Role.STUDENT).only(
            'course_id', 'section_id'
        )
    )

    courses = []
    for enrollment in enrollments:
        names = [
            instructor.user.full_name
            for instructor in instructors
            if instructor.course_id == enrollment.course_id and _teaches(instructor, enrollment)
        ]

        student_count = None
        if enrollment.role == Enrollment.Role.INSTRUCTOR:
            student_count = sum(
                1
                for student in students
                if student.course_id == enrollment.course_id and _counts_toward(student, enrollment)
            )

        courses.append(MyCourse(enrollment, names, student_count))
    return courses


# Students never see drafts (not ready) or archived work (withdrawn).
STUDENT_VISIBLE_STATUSES = (Assignment.Status.PUBLISHED, Assignment.Status.CLOSED)


def get_course_assignments(course_id, role):
    assignments = Assignment.objects.filter(course_id=course_id).order_by('due_at', 'id')
    if role != Enrollment.Role.INSTRUCTOR:
        assignments = assignments.filter(status__in=STUDENT_VISIBLE_STATUSES)
    return assignments
