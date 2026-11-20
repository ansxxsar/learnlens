from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only: audit rows are evidence and must not be edited."""

    list_display = ('created_at', 'action', 'entity_type', 'entity_id', 'actor')
    list_filter = ('action', 'entity_type')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
