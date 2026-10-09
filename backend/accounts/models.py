from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Creates users with email as the login name."""

    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address.')
        user = self.model(email=self.normalize_email(email), full_name=full_name, **extra_fields)
        user.set_password(password)  # stores a hash, never the plain password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields['is_admin'] = True
        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractBaseUser):
    """ERD table "users".

    Columns: id, email, password_hash, full_name, is_admin, is_active, created_at.
    Course roles (student / instructor) live in enrollments, not here.
    """

    email = models.EmailField(max_length=255, unique=True)
    # AbstractBaseUser calls this field "password"; the ERD column is password_hash.
    password = models.CharField(max_length=128, db_column='password_hash')
    full_name = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # The ERD has no last_login column, so remove the one AbstractBaseUser adds.
    last_login = None

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email

    # The Django admin needs these three. They are computed from is_admin,
    # so no extra database columns are required.
    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_admin

    def has_module_perms(self, app_label):
        return self.is_active and self.is_admin
