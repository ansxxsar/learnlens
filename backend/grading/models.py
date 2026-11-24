"""ERD table "criterion_scores": the approved score of one rubric criterion
for one attempt.

Rows exist only once an instructor has approved the grade, so a student
never sees an unapproved score. The automatic suggestion is never final on
its own: an instructor must approve it (AGENTS.md).
"""

from django.conf import settings
from django.db import models

from submissions.models import Submission


class CriterionScore(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='criterion_scores')
    criterion = models.ForeignKey('courses.RubricCriterion', on_delete=models.CASCADE, related_name='scores')
    # The suggestion when the grade was approved. Null when nothing could be
    # suggested, such as a criterion that no test checks.
    auto_points = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    final_points = models.DecimalField(max_digits=6, decimal_places=2)
    # Set when the instructor changed a suggestion; the reason is required.
    overridden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    override_reason = models.TextField(null=True, blank=True)
    overridden_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'criterion_scores'
        constraints = [
            models.UniqueConstraint(fields=['submission', 'criterion'], name='unique_score_per_criterion'),
            models.CheckConstraint(
                condition=models.Q(auto_points__isnull=True) | models.Q(auto_points__gte=0),
                name='auto_points_not_negative',
            ),
            models.CheckConstraint(condition=models.Q(final_points__gte=0), name='final_points_not_negative'),
            models.CheckConstraint(
                condition=models.Q(override_reason__isnull=True, overridden_at__isnull=True)
                | models.Q(override_reason__isnull=False, overridden_at__isnull=False),
                name='override_reason_with_time',
            ),
        ]

    def __str__(self):
        return f'{self.submission} / {self.criterion}: {self.final_points}'
