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


class MyCoursesApiTests(TestCase):
    """GET /courses: the same course shows up for its teacher and its students."""

    def setUp(self):
        self.course = Course.objects.create(code='CSS105', title='Introduction to Programming', term='Fall 2026')
        self.section_a = CourseSection.objects.create(course=self.course, code='01-N')
        self.section_b = CourseSection.objects.create(course=self.course, code='02-N')

        self.teacher_a = self.enroll('Aigerim Teacher', Enrollment.Role.INSTRUCTOR, self.section_a)
        self.teacher_b = self.enroll('Bolat Teacher', Enrollment.Role.INSTRUCTOR, self.section_b)
        self.student_a = self.enroll('Student A', Enrollment.Role.STUDENT, self.section_a)
        self.enroll('Student A2', Enrollment.Role.STUDENT, self.section_a)
        self.enroll('Student B', Enrollment.Role.STUDENT, self.section_b)

    def enroll(self, name, role, section=None, course=None):
        count = get_user_model().objects.count()
        user = get_user_model().objects.create_user(
            email=f'user{count}@sdu.edu.kz', full_name=name, password='test-pass-123'
        )
        Enrollment.objects.create(user=user, course=course or self.course, section=section, role=role)
        return user

    def get_courses(self, user):
        self.client.force_login(user)
        response = self.client.get('/courses')
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_anonymous_request_gets_401(self):
        self.assertEqual(self.client.get('/courses').status_code, 401)

    def test_teacher_and_student_see_the_same_course(self):
        [taught] = self.get_courses(self.teacher_a)
        [studied] = self.get_courses(self.student_a)

        self.assertEqual(taught['id'], studied['id'])
        self.assertEqual(taught['title'], 'Introduction to Programming')
        self.assertEqual(taught['role'], 'instructor')
        self.assertEqual(studied['role'], 'student')

    def test_student_sees_only_their_own_sections_teacher(self):
        [course] = self.get_courses(self.student_a)

        self.assertEqual(course['section_code'], '01-N')
        self.assertEqual(course['instructor_names'], ['Aigerim Teacher'])

    def test_teacher_of_whole_course_is_shown_to_every_student(self):
        self.enroll('Lead Teacher', Enrollment.Role.INSTRUCTOR)

        [course] = self.get_courses(self.student_a)

        self.assertEqual(course['instructor_names'], ['Aigerim Teacher', 'Lead Teacher'])

    def test_teacher_counts_only_students_in_their_section(self):
        [course] = self.get_courses(self.teacher_a)

        self.assertEqual(course['student_count'], 2)

    def test_teacher_of_whole_course_counts_every_student(self):
        lead = self.enroll('Lead Teacher', Enrollment.Role.INSTRUCTOR)

        [course] = self.get_courses(lead)

        self.assertEqual(course['student_count'], 3)

    def test_student_is_not_given_a_student_count(self):
        [course] = self.get_courses(self.student_a)

        self.assertIsNone(course['student_count'])

    def test_courses_the_user_is_not_enrolled_in_are_hidden(self):
        other = Course.objects.create(code='CSS201', title='Data Structures', term='Fall 2026')
        self.enroll('Other Teacher', Enrollment.Role.INSTRUCTOR, course=other)

        codes = [course['code'] for course in self.get_courses(self.student_a)]

        self.assertEqual(codes, ['CSS105'])

    def test_user_without_enrollments_gets_an_empty_list(self):
        newcomer = get_user_model().objects.create_user(
            email='newcomer@sdu.edu.kz', full_name='New User', password='test-pass-123'
        )

        self.assertEqual(self.get_courses(newcomer), [])

    def test_response_never_contains_emails(self):
        for user in (self.teacher_a, self.student_a):
            self.client.force_login(user)
            self.assertNotIn('@', self.client.get('/courses').content.decode())

    def test_query_count_does_not_grow_with_courses(self):
        for number in range(5):
            course = Course.objects.create(code=f'EXTRA{number}', title='Extra', term='Fall 2026')
            Enrollment.objects.create(user=self.student_a, course=course)
            self.enroll('Extra Teacher', Enrollment.Role.INSTRUCTOR, course=course)
        self.client.force_login(self.student_a)

        # session + user + enrollments + instructors + students
        with self.assertNumQueries(5):
            self.client.get('/courses')
