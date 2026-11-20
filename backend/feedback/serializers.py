from rest_framework import serializers


class FeedbackItemSerializer(serializers.Serializer):
    """Messages are written by the rules to be safe for students: hidden tests
    appear only by their number and verdict (feedback/rules.py)."""

    kind = serializers.CharField()
    message = serializers.CharField()
    error_category = serializers.CharField(allow_null=True)
    line_start = serializers.IntegerField(allow_null=True)
    line_end = serializers.IntegerField(allow_null=True)
    criterion_title = serializers.CharField(source='criterion.title', default=None)


class FeedbackSerializer(serializers.Serializer):
    source = serializers.CharField()
    summary = serializers.CharField()
    created_at = serializers.DateTimeField()
    items = FeedbackItemSerializer(many=True)
