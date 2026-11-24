from rest_framework import serializers

from .models import Assignment, Course


class CourseSerializer(serializers.ModelSerializer):
    assignment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "code",
            "title",
            "term",
            "assignment_count",
        )


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = (
            "id",
            "title",
            "instructions",
            "status",
            "feedback_depth",
            "due_at",
            "published_at",
        )