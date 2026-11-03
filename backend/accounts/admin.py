from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import User


class UserCreateForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'full_name')


class UserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'full_name', 'is_admin', 'is_active')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Reuses Django's user admin so passwords are always stored hashed.

    Settings below replace the defaults that refer to fields our User
    does not have (username, groups, is_superuser, ...).
    """

    form = UserEditForm
    add_form = UserCreateForm

    list_display = ('email', 'full_name', 'is_admin', 'is_active', 'created_at')
    list_filter = ('is_admin', 'is_active')
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
