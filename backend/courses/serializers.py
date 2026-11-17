from rest_framework import serializers


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
