"""ERD table "audit_logs" (FR 12): who changed what in assessment, and when.

Rows are only ever added. `details` holds ids and numbers, never code,
override reasons or other personal text.
"""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=50)
    entity_id = models.BigIntegerField()
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [models.Index(fields=['entity_type', 'entity_id'], name='audit_entity_idx')]

    def __str__(self):
        return f'{self.action} {self.entity_type}#{self.entity_id}'


def record(actor, action, entity, details=None):
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        entity_type=entity._meta.db_table,
        entity_id=entity.pk,
        details=details,
    )
