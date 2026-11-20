from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.permissions import IsCourseInstructor

from .selectors import check_can_grade, get_attempt_for_review, get_gradebook, submissions_for_review
from .serializers import ApproveGradeSerializer, gradebook_data, review_data
from .services import approve_grade


class GradebookView(APIView):
    """The instructor's sheet: their students × the course's assignments."""

    permission_classes = [IsCourseInstructor]

    def get(self, request, course_id):
        return Response(gradebook_data(get_gradebook(course_id, request.user)))


class AttemptReviewMixin:
    permission_classes = [IsCourseInstructor]

    def get_attempt(self, request, course_id, assignment_id, submission_id):
        # Scoped to the URL's course and assignment, and to the instructor's
        # own students (their section, or the whole course).
        submission = get_attempt_for_review(course_id, assignment_id, submission_id)
        if submission is None:
            raise Http404
        check_can_grade(course_id, request.user, submission.student_id)
        return submission

    def respond(self, submission):
        others = (
            submissions_for_review()
            .filter(assignment_id=submission.assignment_id, student_id=submission.student_id)
            .order_by('-attempt_number')
        )
        return Response(review_data(submission, others))


class AttemptReviewView(AttemptReviewMixin, APIView):
    """One attempt with its code, all test results, feedback and scores."""

    def get(self, request, course_id, assignment_id, submission_id):
        return self.respond(self.get_attempt(request, course_id, assignment_id, submission_id))


class ApproveGradeView(AttemptReviewMixin, APIView):
    def post(self, request, course_id, assignment_id, submission_id):
        submission = self.get_attempt(request, course_id, assignment_id, submission_id)
        serializer = ApproveGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve_grade(submission, request.user, serializer.to_scores())
        # Re-read so the response shows the saved scores.
        return self.respond(self.get_attempt(request, course_id, assignment_id, submission_id))

