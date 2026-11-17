from django.utils import timezone
from rest_framework import serializers

from .models import Assignment


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
