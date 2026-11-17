from django.contrib import admin

from .models import Submission, SubmissionFile


class SubmissionFileInline(admin.TabularInline):
    model = SubmissionFile
    extra = 0
    # Attempts are immutable: staff can read the code but not change it.
    readonly_fields = ('path', 'content', 'is_entry_point')
    can_delete = False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'attempt_number', 'status', 'submitted_at')
    list_filter = ('status', 'assignment__course')
    search_fields = ('student__email', 'student__full_name', 'assignment__title')
    readonly_fields = ('assignment', 'student', 'attempt_number', 'submitted_at')
    inlines = [SubmissionFileInline]
