from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from accounts.authentication import SessionAuth

from .models import Assignment, Course, CourseSection, Enrollment
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


class CourseAssignmentsApiTests(TestCase):
    """Course page and assignments: instructors manage, students read."""

    def setUp(self):
        self.course = Course.objects.create(code='CSS105', title='Introduction to Programming', term='Fall 2026')
        self.other_course = Course.objects.create(code='CSS201', title='Data Structures', term='Fall 2026')
        self.teacher = self.enroll('Teacher', Enrollment.Role.INSTRUCTOR)
        self.student = self.enroll('Student', Enrollment.Role.STUDENT)
        self.other_teacher = self.enroll('Other Teacher', Enrollment.Role.INSTRUCTOR, course=self.other_course)
        self.due = timezone.now() + timedelta(days=7)

    def enroll(self, name, role, course=None):
        count = get_user_model().objects.count()
        user = get_user_model().objects.create_user(
            email=f'user{count}@sdu.edu.kz', full_name=name, password='test-pass-123'
        )
        Enrollment.objects.create(user=user, course=course or self.course, role=role)
        return user

    def url(self, assignment=None, course=None):
        base = f'/courses/{(course or self.course).id}/assignments'
        return f'{base}/{assignment.id}' if assignment else base

    def make(self, status=Assignment.Status.DRAFT, title='Task', course=None):
        return Assignment.objects.create(
            course=course or self.course, title=title, instructions='Do it.', status=status, due_at=self.due
        )

    def as_user(self, user):
        self.client.force_login(user)
        return self.client

    def create(self, user, **overrides):
        body = {'title': 'Hello world', 'instructions': 'Print a greeting.', 'due_at': self.due.isoformat()}
        body.update(overrides)
        return self.as_user(user).post(self.url(), body, content_type='application/json')

    def patch(self, user, assignment, body):
        return self.as_user(user).patch(self.url(assignment), body, content_type='application/json')

    # Course page

    def test_member_gets_course_detail(self):
        response = self.as_user(self.student).get(f'/courses/{self.course.id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Introduction to Programming')
        self.assertEqual(response.json()['role'], 'student')

    def test_non_member_cannot_open_course(self):
        response = self.as_user(self.other_teacher).get(f'/courses/{self.course.id}')

        self.assertEqual(response.status_code, 403)

    # Listing

    def test_student_sees_only_published_and_closed_assignments(self):
        for status in Assignment.Status.values:
            self.make(status=status, title=status)

        titles = [a['title'] for a in self.as_user(self.student).get(self.url()).json()]

        self.assertCountEqual(titles, ['published', 'closed'])

    def test_instructor_sees_every_assignment(self):
        for status in Assignment.Status.values:
            self.make(status=status, title=status)

        titles = [a['title'] for a in self.as_user(self.teacher).get(self.url()).json()]

        self.assertCountEqual(titles, Assignment.Status.values)

    def test_non_member_cannot_list_assignments(self):
        self.make(status=Assignment.Status.PUBLISHED)

        self.assertEqual(self.as_user(self.other_teacher).get(self.url()).status_code, 403)

    def test_assignment_response_has_no_test_cases(self):
        self.make(status=Assignment.Status.PUBLISHED)

        [assignment] = self.as_user(self.student).get(self.url()).json()

        self.assertNotIn('test_cases', assignment)

    # Creating

    def test_instructor_creates_a_draft_by_default(self):
        response = self.create(self.teacher)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'draft')
        self.assertIsNone(response.json()['published_at'])
        self.assertEqual(Assignment.objects.get().course, self.course)

    def test_instructor_can_publish_on_create(self):
        response = self.create(self.teacher, publish=True)

        self.assertEqual(response.json()['status'], 'published')
        self.assertIsNotNone(response.json()['published_at'])

    def test_student_cannot_create_assignment(self):
        self.assertEqual(self.create(self.student).status_code, 403)
        self.assertFalse(Assignment.objects.exists())

    def test_instructor_of_another_course_cannot_create_here(self):
        self.assertEqual(self.create(self.other_teacher).status_code, 403)

    def test_deadline_must_be_in_the_future(self):
        response = self.create(self.teacher, due_at=(timezone.now() - timedelta(hours=1)).isoformat())

        self.assertEqual(response.status_code, 400)
        self.assertIn('due_at', response.json())

    def test_client_cannot_set_status_or_course_directly(self):
        response = self.create(self.teacher, status='published', course=self.other_course.id)

        self.assertEqual(response.json()['status'], 'draft')
        self.assertEqual(Assignment.objects.get().course, self.course)

    # Updating

    def test_instructor_edits_and_publishes(self):
        assignment = self.make()

        response = self.patch(self.teacher, assignment, {'title': 'Loops', 'status': 'published'})

        self.assertEqual(response.status_code, 200)
        assignment.refresh_from_db()
        self.assertEqual(assignment.title, 'Loops')
        self.assertEqual(assignment.status, 'published')
        self.assertIsNotNone(assignment.published_at)

    def test_reopening_keeps_first_publish_time(self):
        assignment = self.make()
        self.patch(self.teacher, assignment, {'status': 'published'})
        first = Assignment.objects.get().published_at
        self.patch(self.teacher, assignment, {'status': 'closed'})

        self.patch(self.teacher, assignment, {'status': 'published'})

        self.assertEqual(Assignment.objects.get().published_at, first)

    def test_draft_cannot_jump_to_closed(self):
        response = self.patch(self.teacher, self.make(), {'status': 'closed'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('status', response.json())

    def test_published_cannot_go_back_to_draft(self):
        response = self.patch(self.teacher, self.make(Assignment.Status.PUBLISHED), {'status': 'draft'})

        self.assertEqual(response.status_code, 400)

    def test_archived_assignment_cannot_be_changed(self):
        response = self.patch(self.teacher, self.make(Assignment.Status.ARCHIVED), {'title': 'New'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Archived assignments cannot be changed.'})

    def test_student_cannot_update_assignment(self):
        assignment = self.make(Assignment.Status.PUBLISHED)

        self.assertEqual(self.patch(self.student, assignment, {'title': 'Hacked'}).status_code, 403)
        assignment.refresh_from_db()
        self.assertEqual(assignment.title, 'Task')

    def test_assignment_of_another_course_is_not_found_through_this_course(self):
        # The other teacher is an instructor of other_course, so the permission
        # check passes; the lookup must still be scoped to that course.
        foreign = self.make(course=self.course)

        response = self.as_user(self.other_teacher).patch(
            self.url(foreign, course=self.other_course), {'title': 'Hacked'}, content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertEqual(foreign.title, 'Task')

    # Deleting

    def test_instructor_deletes_a_draft(self):
        response = self.as_user(self.teacher).delete(self.url(self.make()))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Assignment.objects.exists())

    def test_published_assignment_cannot_be_deleted(self):
        response = self.as_user(self.teacher).delete(self.url(self.make(Assignment.Status.PUBLISHED)))

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Assignment.objects.exists())

    def test_student_cannot_delete(self):
        response = self.as_user(self.student).delete(self.url(self.make()))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Assignment.objects.exists())
