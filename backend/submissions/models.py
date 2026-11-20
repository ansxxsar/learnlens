"""Submissions tables from docs/erd/learnlens-erd.drawio.

Security: submitted code is hostile input. It is only stored here and must
never be run in the API process; execution belongs to isolated workers.
"""

from django.conf import settings
from django.db import models

from courses.models import Assignment


class Submission(models.Model):
    """ERD table "submissions": one immutable attempt at an assignment."""

    class Status(models.TextChoices):
        QUEUED = 'queued'
        RUNNING = 'running'
        COMPLETED = 'completed'
        FAILED = 'failed'

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    attempt_number = models.IntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'submissions'
        constraints = [
            models.UniqueConstraint(
                fields=['assignment', 'student', 'attempt_number'], name='unique_attempt_per_student'
            ),
            models.CheckConstraint(condition=models.Q(attempt_number__gte=1), name='attempt_number_positive'),
        ]

    def __str__(self):
        return f'{self.student} – {self.assignment} #{self.attempt_number}'


class SubmissionFile(models.Model):
    """ERD table "submission_files". The entry point's extension tells which
    language the attempt is written in (see submissions/languages.py)."""

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='files')
    path = models.CharField(max_length=255)
    content = models.TextField()
    is_entry_point = models.BooleanField(default=False)

    class Meta:
        db_table = 'submission_files'
        constraints = [
            models.UniqueConstraint(fields=['submission', 'path'], name='unique_file_path_per_submission'),
        ]

    def __str__(self):
        return self.path


class TestResult(models.Model):
    """ERD table "test_results": the outcome of one test case for one attempt.

    Security: actual_output and error_output of a hidden test may contain its
    input, so students are only shown whether it passed (see serializers).
    """

    class ErrorType(models.TextChoices):
        WRONG_ANSWER = 'wrong_answer'
        RUNTIME_ERROR = 'runtime_error'
        TIME_LIMIT = 'time_limit'
        MEMORY_LIMIT = 'memory_limit'
        OUTPUT_LIMIT = 'output_limit'
        COMPILE_ERROR = 'compile_error'

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='test_results')
    test_case = models.ForeignKey('courses.TestCase', on_delete=models.CASCADE, related_name='results')
    passed = models.BooleanField()
    actual_output = models.TextField(null=True, blank=True)
    # The compiler's message, or what the program printed to stderr.
    error_output = models.TextField(null=True, blank=True)
    # Empty when the test passed.
    error_type = models.CharField(max_length=50, choices=ErrorType.choices, null=True, blank=True)
    runtime_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'test_results'
        constraints = [
            models.UniqueConstraint(fields=['submission', 'test_case'], name='unique_result_per_test'),
            models.CheckConstraint(
                condition=models.Q(runtime_ms__isnull=True) | models.Q(runtime_ms__gte=0),
                name='runtime_ms_not_negative',
            ),
        ]

    def __str__(self):
        return f'{self.submission} / {self.test_case}: {"passed" if self.passed else self.error_type}'
