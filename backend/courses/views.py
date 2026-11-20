from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Assignment, Enrollment, RubricCriterion, TestCase
from .permissions import IsCourseInstructor, IsCourseMember, get_course_role
from .selectors import get_course_assignments, get_my_courses, get_rubric, get_test_cases, get_visible_assignment
from .serializers import (
    AssignmentCreateSerializer,
    AssignmentSerializer,
    AssignmentUpdateSerializer,
    InstructorTestCaseSerializer,
    MyCourseSerializer,
    PublicTestCaseSerializer,
    RubricCriterionSerializer,
    RubricCriterionWriteSerializer,
    TestCaseWriteSerializer,
)


class MyCoursesView(APIView):
    """The courses the signed-in user teaches or studies. There is no user id
    in the URL, so nobody can list another user's courses."""

    def get(self, request):
        return Response(MyCourseSerializer(get_my_courses(request.user), many=True).data)


class CourseDetailView(APIView):
    permission_classes = [IsCourseMember]

    def get(self, request, course_id):
        [course] = get_my_courses(request.user, course_id=course_id)
        return Response(MyCourseSerializer(course).data)


class CourseAssignmentsView(APIView):
    """Members list assignments; only instructors create them."""

    def get_permissions(self):
        permission = IsCourseInstructor if self.request.method == 'POST' else IsCourseMember
        return [permission()]

    def get(self, request, course_id):
        role = get_course_role(request.user, course_id)
        assignments = get_course_assignments(course_id, request.user, role)
        return Response(AssignmentSerializer(assignments, many=True).data)

    def post(self, request, course_id):
        serializer = AssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = services.create_assignment(course_id, **serializer.validated_data)
        return Response(AssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class AssignmentDetailView(APIView):
    permission_classes = [IsCourseInstructor]

    def get_assignment(self, course_id, assignment_id):
        # Looked up inside the URL's course, so an instructor of one course
        # cannot reach another course's assignment by changing the id.
        return get_object_or_404(Assignment, id=assignment_id, course_id=course_id)

    def patch(self, request, course_id, assignment_id):
        assignment = self.get_assignment(course_id, assignment_id)
        serializer = AssignmentUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        assignment = services.update_assignment(assignment, **serializer.validated_data)
        return Response(AssignmentSerializer(assignment).data)

    def delete(self, request, course_id, assignment_id):
        services.delete_assignment(self.get_assignment(course_id, assignment_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class MembersReadInstructorsWrite:
    """GET for course members, everything else for instructors only."""

    def get_permissions(self):
        permission = IsCourseMember if self.request.method == 'GET' else IsCourseInstructor
        return [permission()]

    def get_assignment(self, request, course_id, assignment_id):
        return get_visible_assignment(course_id, assignment_id, get_course_role(request.user, course_id))


class AssignmentRubricView(MembersReadInstructorsWrite, APIView):
    def get(self, request, course_id, assignment_id):
        assignment = self.get_assignment(request, course_id, assignment_id)
        return Response(RubricCriterionSerializer(get_rubric(assignment), many=True).data)

    def post(self, request, course_id, assignment_id):
        assignment = self.get_assignment(request, course_id, assignment_id)
        serializer = RubricCriterionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        criterion = services.create_criterion(assignment, **serializer.validated_data)
        return Response(RubricCriterionSerializer(criterion).data, status=status.HTTP_201_CREATED)


class RubricCriterionDetailView(APIView):
    permission_classes = [IsCourseInstructor]

    def get_criterion(self, course_id, assignment_id, criterion_id):
        # Scoped to the URL's course and assignment, like AssignmentDetailView.
        return get_object_or_404(
            RubricCriterion.objects.select_related('assignment'),
            id=criterion_id,
            assignment_id=assignment_id,
            assignment__course_id=course_id,
        )

    def patch(self, request, course_id, assignment_id, criterion_id):
        criterion = self.get_criterion(course_id, assignment_id, criterion_id)
        serializer = RubricCriterionWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        criterion = services.update_criterion(criterion, **serializer.validated_data)
        return Response(RubricCriterionSerializer(criterion).data)

    def delete(self, request, course_id, assignment_id, criterion_id):
        services.delete_criterion(self.get_criterion(course_id, assignment_id, criterion_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignmentTestsView(MembersReadInstructorsWrite, APIView):
    """Instructors get every test; students get only the public ones."""

    def get(self, request, course_id, assignment_id):
        role = get_course_role(request.user, course_id)
        assignment = get_visible_assignment(course_id, assignment_id, role)
        serializer_class = (
            InstructorTestCaseSerializer if role == Enrollment.Role.INSTRUCTOR else PublicTestCaseSerializer
        )
        return Response(serializer_class(get_test_cases(assignment, role), many=True).data)

    def post(self, request, course_id, assignment_id):
        assignment = self.get_assignment(request, course_id, assignment_id)
        serializer = TestCaseWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        test_case = services.create_test_case(assignment, **serializer.validated_data)
        return Response(InstructorTestCaseSerializer(test_case).data, status=status.HTTP_201_CREATED)


class TestCaseDetailView(APIView):
    permission_classes = [IsCourseInstructor]

    def get_test_case(self, course_id, assignment_id, test_id):
        return get_object_or_404(
            TestCase.objects.select_related('assignment'),
            id=test_id,
            assignment_id=assignment_id,
            assignment__course_id=course_id,
        )

    def patch(self, request, course_id, assignment_id, test_id):
        test_case = self.get_test_case(course_id, assignment_id, test_id)
        serializer = TestCaseWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        test_case = services.update_test_case(test_case, **serializer.validated_data)
        return Response(InstructorTestCaseSerializer(test_case).data)

    def delete(self, request, course_id, assignment_id, test_id):
        services.delete_test_case(self.get_test_case(course_id, assignment_id, test_id))
        return Response(status=status.HTTP_204_NO_CONTENT)
