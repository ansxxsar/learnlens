from rest_framework import serializers

from .models import User


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    # Passwords are compared exactly, so surrounding spaces must be kept.
    password = serializers.CharField(max_length=4096, trim_whitespace=False)


class EnrollmentSummarySerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    course_code = serializers.CharField(source='course.code')
    course_title = serializers.CharField(source='course.title')
    section_code = serializers.CharField(source='section.code', default=None)
    role = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """The signed-in user's own profile. Fields are listed explicitly so new
    User columns, and the password hash, are never exposed by accident."""

    enrollments = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'is_admin', 'enrollments']

    def get_enrollments(self, user):
        enrollments = user.enrollments.select_related('course', 'section').order_by('course__code')
        return EnrollmentSummarySerializer(enrollments, many=True).data
