"""Read-only queries for attempts and daily progress.

Daily progress is a learning habit tracker, kept apart from grades: it only
counts whether a student submitted, never whether the work was correct.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from courses.models import Assignment, Enrollment

from .models import Submission

WEEK_DAYS = 7


def get_my_attempts(assignment, student):
    return (
        Submission.objects.filter(assignment=assignment, student=student)
        .prefetch_related('files', 'test_results__test_case')
        .order_by('-attempt_number')
    )


@dataclass(frozen=True)
class ProgressTask:
    assignment: Assignment
    is_done: bool


@dataclass(frozen=True)
class DailyProgress:
    today: date
    streak_days: int
    practiced_today: bool
    week: list[tuple[date, int]]
    tasks: list[ProgressTask]


def _streak(active_days, today):
    """Days in a row with at least one attempt. The streak is still alive
    when today has none yet, so it counts back from yesterday then."""
    day = today if today in active_days else today - timedelta(days=1)
    streak = 0
    while day in active_days:
        streak += 1
        day -= timedelta(days=1)
    return streak


def get_daily_progress(student):
    today = timezone.localdate()

    # Days are cut in settings.TIME_ZONE, so late-evening work counts for the
    # day the student actually did it.
    per_day = dict(
        Submission.objects.filter(student=student)
        .annotate(day=TruncDate('submitted_at', tzinfo=timezone.get_current_timezone()))
        .values('day')
        .annotate(count=Count('id'))
        .values_list('day', 'count')
    )
    week = [
        (today - timedelta(days=offset), per_day.get(today - timedelta(days=offset), 0))
        for offset in range(WEEK_DAYS - 1, -1, -1)
    ]

    # Open work in the courses the user studies, soonest deadline first.
    student_course_ids = Enrollment.objects.filter(user=student, role=Enrollment.Role.STUDENT).values(
        'course_id'
    )
    assignments = (
        Assignment.objects.filter(course_id__in=student_course_ids, status=Assignment.Status.PUBLISHED)
        .select_related('course')
        .order_by('due_at', 'id')
    )
    done_ids = set(
        Submission.objects.filter(student=student, assignment__in=assignments).values_list(
            'assignment_id', flat=True
        )
    )
    tasks = [ProgressTask(assignment, assignment.id in done_ids) for assignment in assignments]

    return DailyProgress(
        today=today,
        streak_days=_streak(set(per_day), today),
        practiced_today=today in per_day,
        week=week,
        tasks=tasks,
    )
