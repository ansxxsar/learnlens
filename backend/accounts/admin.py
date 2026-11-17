from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import User
from .roles import STUDENT_EMAIL_PATTERN


class UserCreateForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'full_name')


class UserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'full_name', 'is_admin', 'is_active')


class TeachersWithoutCourseFilter(admin.SimpleListFilter):
    """Accounts with a name-based email and no enrollment yet. They see the
    teacher page but have no courses until an enrollment with the instructor
    role is added. Check that the person really is a teacher first, because
    registration does not verify email ownership."""

    title = 'teacher course'
    parameter_name = 'teacher_course'

    def lookups(self, request, model_admin):
        return [('none', 'Teachers without a course')]

    def queryset(self, request, queryset):
        if self.value() == 'none':
            return queryset.filter(is_admin=False, enrollments__isnull=True).exclude(
                email__regex=STUDENT_EMAIL_PATTERN
            )
        return queryset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Reuses Django's user admin so passwords are always stored hashed.

    Settings below replace the defaults that refer to fields our User
    does not have (username, groups, is_superuser, ...).
    """

    form = UserEditForm
    add_form = UserCreateForm

    list_display = ('email', 'full_name', 'is_admin', 'is_active', 'created_at')
    list_filter = (TeachersWithoutCourseFilter, 'is_admin', 'is_active')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    filter_horizontal = ()
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Profile', {'fields': ('full_name',)}),
        ('Access', {'fields': ('is_admin', 'is_active')}),
        ('Dates', {'fields': ('created_at',)}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'full_name', 'usable_password', 'password1', 'password2')}),
    )
