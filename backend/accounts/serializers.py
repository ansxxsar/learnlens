from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import User
from .roles import get_account_type, is_registration_email_allowed

DUPLICATE_EMAIL_MESSAGE = 'An account with this email already exists.'


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    # Passwords are compared exactly, so surrounding spaces must be kept.
    password = serializers.CharField(max_length=4096, trim_whitespace=False)


class RegisterSerializer(serializers.Serializer):
    """Creates a plain account. Only these three fields are accepted, so a request
    cannot make itself an admin. Course roles still come from enrollments."""

    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=4096, trim_whitespace=False)

    def validate_email(self, value):
        email = User.objects.normalize_email(value)
        if not is_registration_email_allowed(email):
            raise serializers.ValidationError(f'Use your @{settings.REGISTRATION_EMAIL_DOMAIN} email.')
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(DUPLICATE_EMAIL_MESSAGE)
        return email

    def validate(self, attrs):
        user = User(email=attrs['email'], full_name=attrs['full_name'])
        try:
            validate_password(attrs['password'], user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({'password': error.messages})
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return User.objects.create_user(**validated_data)
        except IntegrityError:
            # Two requests with the same email can both pass validate_email.
            raise serializers.ValidationError({'email': [DUPLICATE_EMAIL_MESSAGE]})


class EnrollmentSummarySerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    course_code = serializers.CharField(source='course.code')
    course_title = serializers.CharField(source='course.title')
    section_code = serializers.CharField(source='section.code', default=None)
    role = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """The signed-in user's own profile. Fields are listed explicitly so new
    User columns, and the password hash, are never exposed by accident."""

    account_type = serializers.SerializerMethodField()
    enrollments = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'is_admin', 'account_type', 'enrollments']

    def get_account_type(self, user):
        return get_account_type(user)

    def get_enrollments(self, user):
        enrollments = user.enrollments.select_related('course', 'section').order_by('course__code')
        return EnrollmentSummarySerializer(enrollments, many=True).data
