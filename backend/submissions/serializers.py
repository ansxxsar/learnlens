from django.utils import timezone
from rest_framework import serializers

from .languages import LANGUAGE_BY_FILE, LANGUAGE_CHOICES

# Generous for beginner exercises, small enough that one request cannot fill
# the database.
MAX_CODE_LENGTH = 50_000


class SubmissionCreateSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES)
    # Kept exactly as typed: whitespace matters in code (Python indentation).
    code = serializers.CharField(max_length=MAX_CODE_LENGTH, trim_whitespace=False)

    def validate_code(self, value):
        if not value.strip():
            raise serializers.ValidationError('Write some code before submitting.')
        return value


class SubmissionSerializer(serializers.Serializer):
    """One of the student's own attempts, including their own code."""

    id = serializers.IntegerField()
    attempt_number = serializers.IntegerField()
    status = serializers.CharField()
    submitted_at = serializers.DateTimeField()
    language = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()

    def _entry(self, submission):
        return next((file for file in submission.files.all() if file.is_entry_point), None)

    def get_language(self, submission):
        entry = self._entry(submission)
        return LANGUAGE_BY_FILE.get(entry.path) if entry else None

    def get_code(self, submission):
        entry = self._entry(submission)
        return entry.content if entry else ''


class ProgressTaskSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField(source='assignment.id')
    course_id = serializers.IntegerField(source='assignment.course_id')
    course_code = serializers.CharField(source='assignment.course.code')
    title = serializers.CharField(source='assignment.title')
    due_at = serializers.DateTimeField(source='assignment.due_at')
    is_done = serializers.BooleanField()
    is_overdue = serializers.SerializerMethodField()

    def get_is_overdue(self, task):
        return not task.is_done and task.assignment.due_at < timezone.now()


class WeekDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    submissions = serializers.IntegerField()


class DailyProgressSerializer(serializers.Serializer):
    today = serializers.DateField()
    streak_days = serializers.IntegerField()
    practiced_today = serializers.BooleanField()
    week = serializers.SerializerMethodField()
    tasks = ProgressTaskSerializer(many=True)
    completed_tasks = serializers.SerializerMethodField()
    total_tasks = serializers.SerializerMethodField()

    def get_week(self, progress):
        return WeekDaySerializer(
            [{'date': day, 'submissions': count} for day, count in progress.week], many=True
        ).data

    def get_completed_tasks(self, progress):
        return sum(task.is_done for task in progress.tasks)

    def get_total_tasks(self, progress):
        return len(progress.tasks)
