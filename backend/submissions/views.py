from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from courses.models import Assignment
from courses.permissions import IsCourseStudent
from courses.selectors import STUDENT_VISIBLE_STATUSES

from .selectors import get_daily_progress, get_my_attempts
from .serializers import DailyProgressSerializer, SubmissionCreateSerializer, SubmissionSerializer
from .services import create_submission


class MyAttemptsView(APIView):
    """A student's own attempts at one assignment. Only students submit;
    there is no student id in the URL, so nobody sees another's code."""

    permission_classes = [IsCourseStudent]
    throttle_scope = 'submission'

    def get_throttles(self):
        return [ScopedRateThrottle()] if self.request.method == 'POST' else []

    def get_assignment(self, course_id, assignment_id):
        # Scoped to the URL's course and to what students may see, so drafts
        # and other courses' assignments answer 404.
        return get_object_or_404(
            Assignment, id=assignment_id, course_id=course_id, status__in=STUDENT_VISIBLE_STATUSES
        )

    def get(self, request, course_id, assignment_id):
        assignment = self.get_assignment(course_id, assignment_id)
        return Response(SubmissionSerializer(get_my_attempts(assignment, request.user), many=True).data)

    def post(self, request, course_id, assignment_id):
        assignment = self.get_assignment(course_id, assignment_id)
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = create_submission(assignment, request.user, **serializer.validated_data)
        # Re-read with its file so the response shows the language and code.
        submission = get_my_attempts(assignment, request.user).get(id=submission.id)
        return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)


class MyProgressView(APIView):
    """The signed-in user's own daily progress."""

    def get(self, request):
        return Response(DailyProgressSerializer(get_daily_progress(request.user)).data)
