from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Assignment
from .permissions import IsCourseInstructor, IsCourseMember, get_course_role
from .selectors import get_course_assignments, get_my_courses
from .serializers import (
    AssignmentCreateSerializer,
    AssignmentSerializer,
    AssignmentUpdateSerializer,
    MyCourseSerializer,
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
        assignments = get_course_assignments(course_id, role)
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
