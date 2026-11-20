"""Feedback tables from docs/erd/learnlens-erd.drawio.

Feedback explains an attempt; it is never a grade. Every item must rest on
evidence the student can check: a test result, a rubric criterion or a line
of their own code (AGENTS.md).
"""

from django.db import models

from submissions.models import Submission, SubmissionFile, TestResult


class Feedback(models.Model):
    """ERD table "feedback": one per attempt."""

    class Source(models.TextChoices):
        # Built by fixed rules from test results (feedback/rules.py). This is
        # also the fallback whenever AI feedback is unavailable.
        RULES = 'rules'
        AI = 'ai'

    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='feedback')
    source = models.CharField(max_length=10, choices=Source.choices)
    summary = models.TextField()
    model_name = models.CharField(max_length=100, null=True, blank=True)
    prompt_version = models.CharField(max_length=20, null=True, blank=True)
    # Which evidence format the feedback was built from, so old feedback can
    # be told apart after the rules change.
    evidence_version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedback'
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(source='ai')
                | (models.Q(model_name__isnull=False) & models.Q(prompt_version__isnull=False)),
                name='ai_feedback_records_model_and_prompt',
            ),
        ]

    def __str__(self):
        return f'Feedback for {self.submission}'


class FeedbackItem(models.Model):
    """ERD table "feedback_items": one strength, issue or next step."""

    class Kind(models.TextChoices):
        STRENGTH = 'strength'
        ISSUE = 'issue'
        NEXT_STEP = 'next_step'

    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='items')
    criterion = models.ForeignKey(
        'courses.RubricCriterion', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_items'
    )
    test_result = models.ForeignKey(
        TestResult, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_items'
    )
    file = models.ForeignKey(
        SubmissionFile, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_items'
    )
    kind = models.CharField(max_length=12, choices=Kind.choices)
    message = models.TextField()
    error_category = models.CharField(max_length=50, null=True, blank=True)
    line_start = models.IntegerField(null=True, blank=True)
    line_end = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'feedback_items'
        ordering = ['id']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(line_start__isnull=True) | models.Q(line_start__gte=1),
                name='line_start_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(line_end__isnull=True) | models.Q(line_end__gte=models.F('line_start')),
                name='line_end_after_start',
            ),
        ]

    def __str__(self):
        return f'{self.kind}: {self.message[:40]}'
