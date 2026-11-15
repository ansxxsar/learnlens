from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from accounts.authentication import SessionAuth

from .models import Course, CourseSection, Enrollment
from .permissions import IsCourseInstructor, IsCourseMember


class CourseSetupConstraintTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='student@example.com', full_name='Test Student', password='test-pass-123'
        )
        self.course = Course.objects.create(code='CS101', title='Intro to Programming', term='Fall 2026')

    def test_user_cannot_enroll_twice_in_same_course(self):
        Enrollment.objects.create(user=self.user, course=self.course)

        # The database rejects the duplicate (unique user_id + course_id).
        with self.assertRaises(IntegrityError), transaction.atomic():
            Enrollment.objects.create(user=self.user, course=self.course)

    def test_sections_in_one_course_cannot_share_a_code(self):
        CourseSection.objects.create(course=self.course, code='A')

        with self.assertRaises(IntegrityError), transaction.atomic():
            CourseSection.objects.create(course=self.course, code='A')

    def test_same_section_code_is_allowed_in_different_courses(self):
        other_course = Course.objects.create(code='CS102', title='Data Structures', term='Fall 2026')
        CourseSection.objects.create(course=self.course, code='A')
        CourseSection.objects.create(course=other_course, code='A')  # no error

        self.assertEqual(CourseSection.objects.filter(code='A').count(), 2)

    def test_enrollment_cannot_use_section_from_another_course(self):
        other_course = Course.objects.create(code='CS102', title='Data Structures', term='Fall 2026')
        other_section = CourseSection.objects.create(course=other_course, code='A')

        with self.assertRaises(ValidationError):
            Enrollment.objects.create(user=self.user, course=self.course, section=other_section)
        self.assertFalse(Enrollment.objects.exists())

    def test_enrollment_can_use_section_from_same_course(self):
        section = CourseSection.objects.create(course=self.course, code='A')

        enrollment = Enrollment.objects.create(user=self.user, course=self.course, section=section)

        self.assertEqual(enrollment.section, section)


class StubCourseView(APIView):
    def get(self, request, course_id):
        return Response(status=204)


class CoursePermissionTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(code='CS101', title='Intro to Programming', term='Fall 2026')
        self.other_course = Course.objects.create(code='CS102', title='Data Structures', term='Fall 2026')

    def status_for(self, permission, user=None, course=None):
        request = APIRequestFactory().get('/')
        if user:
            force_authenticate(request, user=user)
        view = StubCourseView.as_view(permission_classes=[permission], authentication_classes=[SessionAuth])
        return view(request, course_id=(course or self.course).id).status_code

    def make_user(self, role=None, course=None, **extra):
        count = get_user_model().objects.count()
        user = get_user_model().objects.create_user(
            email=f'user{count}@example.com', full_name='Test User', password='test-pass-123', **extra
        )
        if role:
            Enrollment.objects.create(user=user, course=course or self.course, role=role)
        return user

    def test_anonymous_request_gets_401(self):
        self.assertEqual(self.status_for(IsCourseMember), 401)
        self.assertEqual(self.status_for(IsCourseInstructor), 401)

    def test_student_is_member_but_not_instructor(self):
        student = self.make_user(Enrollment.Role.STUDENT)

        self.assertEqual(self.status_for(IsCourseMember, student), 204)
        self.assertEqual(self.status_for(IsCourseInstructor, student), 403)

    def test_instructor_passes_both(self):
        instructor = self.make_user(Enrollment.Role.INSTRUCTOR)

        self.assertEqual(self.status_for(IsCourseMember, instructor), 204)
        self.assertEqual(self.status_for(IsCourseInstructor, instructor), 204)

    def test_role_in_one_course_gives_nothing_in_another(self):
        instructor = self.make_user(Enrollment.Role.INSTRUCTOR, course=self.other_course)

        self.assertEqual(self.status_for(IsCourseMember, instructor), 403)
        self.assertEqual(self.status_for(IsCourseInstructor, instructor), 403)

    def test_admin_without_enrollment_is_denied(self):
        admin = self.make_user(is_admin=True)

        self.assertEqual(self.status_for(IsCourseMember, admin), 403)
