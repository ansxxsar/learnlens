"""Course-level authorization (FR 2).

Views using these classes must have a `course_id` URL argument. A missing one
raises an error instead of allowing the request.
"""

from rest_framework.permissions import BasePermission

from .models import Enrollment


def get_course_role(user, course_id):
    """Returns the user's role in the course, or None if not enrolled."""
    return Enrollment.objects.filter(user=user, course_id=course_id).values_list('role', flat=True).first()


class CourseRolePermission(BasePermission):
    """Allows only users enrolled in the course with one of `allowed_roles`.

    is_admin deliberately grants nothing here: student data is restricted by
    course role, so an admin who needs course access must be enrolled.
    """

    allowed_roles = ()

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return get_course_role(request.user, view.kwargs['course_id']) in self.allowed_roles


class IsCourseMember(CourseRolePermission):
    allowed_roles = (Enrollment.Role.STUDENT, Enrollment.Role.INSTRUCTOR)


class IsCourseInstructor(CourseRolePermission):
    allowed_roles = (Enrollment.Role.INSTRUCTOR,)
