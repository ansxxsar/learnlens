from pathlib import PurePosixPath

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import serializers

from .models import LANGUAGE_CHOICES, User
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


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """The only fields a user may change directly. Email is left out on purpose:
    it decides the account type, so changing it could change someone's role."""

    preferred_language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, allow_blank=True, required=False)

    class Meta:
        model = User
        fields = ['full_name', 'preferred_language']


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=4096, trim_whitespace=False)
    new_password = serializers.CharField(max_length=4096, trim_whitespace=False)

    def validate_current_password(self, value):
        if not self.context['user'].check_password(value):
            raise serializers.ValidationError('Your current password is not correct.')
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value, self.context['user'])
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)
        return value


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
    photo_url = serializers.SerializerMethodField()
    enrollments = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'is_admin',
            'account_type',
            'photo_url',
            'preferred_language',
            'created_at',
            'enrollments',
        ]

    def get_account_type(self, user):
        return get_account_type(user)

    def get_photo_url(self, user):
        if not user.photo:
            return None
        # Each upload has a new random name, so this also refreshes browser caches.
        return f"{reverse('auth-photo')}?v={PurePosixPath(user.photo.name).stem}"

    def get_enrollments(self, user):
        enrollments = user.enrollments.select_related('course', 'section').order_by('course__code')
        return EnrollmentSummarySerializer(enrollments, many=True).data
