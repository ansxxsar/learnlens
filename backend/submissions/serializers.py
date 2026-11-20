from django.utils import timezone
from rest_framework import serializers

from courses.models import TestCase

from .languages import LANGUAGE_BY_FILE, LANGUAGE_CHOICES
from .models import TestResult

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


class StudentTestResultSerializer(serializers.Serializer):
    """One test result as the student sees it.

    Security: a hidden test's output may echo its input, so for hidden tests
    only the verdict is sent. The one exception is a compiler message, which
    comes from the student's code alone and is the same for every test.
    """

    test_name = serializers.SerializerMethodField()
    is_hidden = serializers.SerializerMethodField()
    passed = serializers.BooleanField()
    error_type = serializers.CharField(allow_null=True)
    runtime_ms = serializers.IntegerField(allow_null=True)
    stdin_input = serializers.SerializerMethodField()
    expected_output = serializers.SerializerMethodField()
    actual_output = serializers.SerializerMethodField()
    error_output = serializers.SerializerMethodField()

    def _hidden(self, result):
        return result.test_case.visibility == TestCase.Visibility.HIDDEN

    def get_is_hidden(self, result):
        return self._hidden(result)

    def get_test_name(self, result):
        # Hidden test names can describe the secret input, so they get a number.
        if self._hidden(result):
            return f'Hidden test {self.context["hidden_numbers"][result.id]}'
        return result.test_case.name

    def get_stdin_input(self, result):
        return None if self._hidden(result) else result.test_case.stdin_input

    def get_expected_output(self, result):
        return None if self._hidden(result) else result.test_case.expected_output

    def get_actual_output(self, result):
        return None if self._hidden(result) else result.actual_output

    def get_error_output(self, result):
        if self._hidden(result) and result.error_type != TestResult.ErrorType.COMPILE_ERROR:
            return None
        return result.error_output


class SubmissionSerializer(serializers.Serializer):
    """One of the student's own attempts, including their own code and its
    test results."""

    id = serializers.IntegerField()
    attempt_number = serializers.IntegerField()
    status = serializers.CharField()
    submitted_at = serializers.DateTimeField()
    language = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()

    passed_count = serializers.SerializerMethodField()
    test_count = serializers.SerializerMethodField()
    results = serializers.SerializerMethodField()

    def _results(self, submission):
        return sorted(submission.test_results.all(), key=lambda result: result.test_case_id)

    def get_passed_count(self, submission):
        return sum(result.passed for result in submission.test_results.all())

    def get_test_count(self, submission):
        return len(submission.test_results.all())

    def get_results(self, submission):
        results = self._results(submission)
        hidden = [result for result in results if result.test_case.visibility == TestCase.Visibility.HIDDEN]
        numbers = {result.id: index for index, result in enumerate(hidden, start=1)}
        return StudentTestResultSerializer(results, many=True, context={'hidden_numbers': numbers}).data

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
