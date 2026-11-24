from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Assignment, Course, Enrollment
from .serializers import AssignmentSerializer, CourseSerializer


class StudentCourseListView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Course.objects.filter(
                enrollments__user=self.request.user,
                enrollments__role=Enrollment.Role.STUDENT,
            )
            .annotate(assignment_count=Count("assignments", distinct=True))
            .order_by("code")
        )


class StudentCourseAssignmentListView(generics.ListAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        course = get_object_or_404(
            Course.objects.filter(
                enrollments__user=self.request.user,
                enrollments__role=Enrollment.Role.STUDENT,
            ),
            pk=self.kwargs["course_id"],
        )

        return Assignment.objects.filter(
            course=course,
            status=Assignment.Status.PUBLISHED,
        ).order_by("due_at", "id")