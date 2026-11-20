from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import Assignment, TestCase


class MyCourseSerializer(serializers.Serializer):
    """One course from the signed-in user's point of view. Fields are listed
    explicitly; instructors are shown by name only, never by email."""

    id = serializers.IntegerField(source='enrollment.course.id')
    code = serializers.CharField(source='enrollment.course.code')
    title = serializers.CharField(source='enrollment.course.title')
    term = serializers.CharField(source='enrollment.course.term')
    role = serializers.CharField(source='enrollment.role')
    section_code = serializers.CharField(source='enrollment.section.code', default=None)
    instructor_names = serializers.ListField(child=serializers.CharField())
    student_count = serializers.IntegerField(allow_null=True)


class AssignmentSerializer(serializers.Serializer):
    """What course members see. Test cases are not part of this, so hidden
    tests can never leak through it."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    instructions = serializers.CharField()
    status = serializers.CharField()
    feedback_depth = serializers.CharField()
    due_at = serializers.DateTimeField()
    published_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    # The requesting student's own attempts; null for instructors.
    attempt_count = serializers.IntegerField(default=None)


class AssignmentWriteSerializer(serializers.Serializer):
    """The fields an instructor may set. course, published_at and created_at
    are set by the server only."""

    title = serializers.CharField(max_length=255)
    instructions = serializers.CharField(max_length=20000)
    due_at = serializers.DateTimeField()
    feedback_depth = serializers.ChoiceField(choices=Assignment.FeedbackDepth.choices, required=False)

    def validate_due_at(self, value):
        # Only checked when the deadline is set or changed, so an assignment
        # whose deadline has passed can still be edited and closed.
        if value <= timezone.now():
            raise serializers.ValidationError('The deadline must be in the future.')
        return value


class AssignmentCreateSerializer(AssignmentWriteSerializer):
    publish = serializers.BooleanField(default=False)


class AssignmentUpdateSerializer(AssignmentWriteSerializer):
    status = serializers.ChoiceField(choices=Assignment.Status.choices, required=False)


class RubricCriterionSerializer(serializers.Serializer):
    """A rubric criterion. Course members may read the rubric, so students
    know how their work is judged."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    max_points = serializers.DecimalField(max_digits=6, decimal_places=2, coerce_to_string=False)
    position = serializers.IntegerField()


class RubricCriterionWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=2000, allow_blank=True, required=False)
    max_points = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.01'), max_value=Decimal('1000')
    )
    position = serializers.IntegerField(min_value=0, required=False)


class InstructorTestCaseSerializer(serializers.Serializer):
    """Every field of a test case, hidden ones included. Instructors only."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    visibility = serializers.CharField()
    stdin_input = serializers.CharField()
    expected_output = serializers.CharField()
    weight = serializers.DecimalField(max_digits=6, decimal_places=2, coerce_to_string=False)
    time_limit_ms = serializers.IntegerField()
    criterion = serializers.IntegerField(source='criterion_id', allow_null=True)


class PublicTestCaseSerializer(serializers.Serializer):
    """A public test as students see it: an example input and output.

    Security: only ever given public tests (see selectors.get_test_cases).
    Hidden tests are never serialized for students.
    """

    id = serializers.IntegerField()
    name = serializers.CharField()
    stdin_input = serializers.CharField()
    expected_output = serializers.CharField()


# Enough for beginner exercises. Larger data belongs in files, not in a row.
MAX_TEST_IO_LENGTH = 20_000


class TestCaseWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    visibility = serializers.ChoiceField(choices=TestCase.Visibility.choices, required=False)
    # Kept exactly as typed: spaces and newlines are part of the expected output.
    stdin_input = serializers.CharField(
        max_length=MAX_TEST_IO_LENGTH, allow_blank=True, trim_whitespace=False, required=False
    )
    expected_output = serializers.CharField(
        max_length=MAX_TEST_IO_LENGTH, allow_blank=True, trim_whitespace=False, required=False
    )
    weight = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.01'), max_value=Decimal('1000'), required=False
    )
    # Capped so one test cannot hold an execution worker for long.
    time_limit_ms = serializers.IntegerField(min_value=100, max_value=10_000, required=False)
    criterion = serializers.IntegerField(allow_null=True, required=False)
