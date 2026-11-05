"""Registration and account type rules, based on SDU email addresses.

The email only decides what a new account starts as. Teacher access always
comes from an instructor enrollment, which only an admin can create, because
registration is open and does not yet prove that someone owns the address.
"""

import re

from django.conf import settings

STUDENT_EMAIL_PATTERN = r'^[0-9]'


class AccountType:
    STUDENT = 'student'
    TEACHER = 'teacher'
    PENDING_TEACHER = 'pending_teacher'
    ADMIN = 'admin'


def is_registration_email_allowed(email):
    # Compares the whole domain, so "x@sdu.edu.kz.evil.com" and "x@notsdu.edu.kz" fail.
    return email.rpartition('@')[2].lower() == settings.REGISTRATION_EMAIL_DOMAIN


def is_student_email(email):
    return re.match(STUDENT_EMAIL_PATTERN, email) is not None


def get_account_type(user):
    roles = set(user.enrollments.values_list('role', flat=True))

    if 'instructor' in roles:
        return AccountType.TEACHER
    if user.is_admin:
        return AccountType.ADMIN
    if roles or is_student_email(user.email):
        return AccountType.STUDENT
    return AccountType.PENDING_TEACHER
