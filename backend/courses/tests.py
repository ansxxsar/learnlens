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

from .models import Assignment, Course, CourseSection, Enrollment, RubricCriterion
from .models import TestCase as TestCaseModel  # django.test.TestCase is already TestCase here
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


class RubricAndTestsApiTests(TestCase):
    """Instructors manage an assignment's rubric and tests. Students read the
    rubric and only the public tests; hidden tests never reach them."""

    def setUp(self):
        self.course = Course.objects.create(code='CSS105', title='Introduction to Programming', term='Fall 2026')
        self.other_course = Course.objects.create(code='CSS201', title='Data Structures', term='Fall 2026')
        self.teacher = self.enroll('Teacher', Enrollment.Role.INSTRUCTOR)
        self.student = self.enroll('Student', Enrollment.Role.STUDENT)
        self.other_teacher = self.enroll('Other Teacher', Enrollment.Role.INSTRUCTOR, course=self.other_course)
        self.assignment = self.make(Assignment.Status.PUBLISHED)

    def enroll(self, name, role, course=None):
        count = get_user_model().objects.count()
        user = get_user_model().objects.create_user(
            email=f'user{count}@sdu.edu.kz', full_name=name, password='test-pass-123'
        )
        Enrollment.objects.create(user=user, course=course or self.course, role=role)
        return user

    def make(self, status, course=None):
        return Assignment.objects.create(
            course=course or self.course,
            title='Sum two numbers',
            instructions='Read two numbers and print their sum.',
            status=status,
            due_at=timezone.now() + timedelta(days=7),
        )

    def url(self, kind, item=None, assignment=None):
        assignment = assignment or self.assignment
        base = f'/courses/{assignment.course_id}/assignments/{assignment.id}/{kind}'
        return f'{base}/{item.id}' if item else base

    def as_user(self, user):
        self.client.force_login(user)
        return self.client

    def post(self, user, kind, body, assignment=None):
        url = self.url(kind, assignment=assignment)
        return self.as_user(user).post(url, body, content_type='application/json')

    def patch(self, user, kind, item, body):
        return self.as_user(user).patch(self.url(kind, item), body, content_type='application/json')

    def criterion(self, title='Correct output', points='5', position=0, assignment=None):
        return RubricCriterion.objects.create(
            assignment=assignment or self.assignment, title=title, max_points=points, position=position
        )

    def test_case(self, name='Example', visibility=TestCaseModel.Visibility.PUBLIC, **fields):
        return TestCaseModel.objects.create(assignment=self.assignment, name=name, visibility=visibility, **fields)

    # Rubric

    def test_instructor_adds_criteria_to_the_end_of_the_rubric(self):
        first = self.post(self.teacher, 'rubric', {'title': 'Correct output', 'max_points': '6'})
        second = self.post(self.teacher, 'rubric', {'title': 'Readable code', 'max_points': 4})

        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.json()['max_points'], 6)
        self.assertEqual([first.json()['position'], second.json()['position']], [0, 1])

    def test_rubric_is_listed_in_position_order(self):
        self.criterion('Second', position=1)
        self.criterion('First', position=0)

        titles = [c['title'] for c in self.as_user(self.student).get(self.url('rubric')).json()]

        self.assertEqual(titles, ['First', 'Second'])

    def test_criterion_points_must_be_positive(self):
        response = self.post(self.teacher, 'rubric', {'title': 'Nothing', 'max_points': 0})

        self.assertEqual(response.status_code, 400)
        self.assertIn('max_points', response.json())

    def test_instructor_edits_and_deletes_a_criterion(self):
        criterion = self.criterion()

        edited = self.patch(self.teacher, 'rubric', criterion, {'title': 'Correct sum'})
        deleted = self.as_user(self.teacher).delete(self.url('rubric', criterion))

        self.assertEqual(edited.json()['title'], 'Correct sum')
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(RubricCriterion.objects.exists())

    def test_deleting_a_criterion_keeps_its_tests(self):
        criterion = self.criterion()
        test_case = self.test_case(criterion=criterion)

        self.as_user(self.teacher).delete(self.url('rubric', criterion))

        test_case.refresh_from_db()
        self.assertIsNone(test_case.criterion_id)

    def test_student_cannot_change_the_rubric(self):
        criterion = self.criterion()

        self.assertEqual(self.post(self.student, 'rubric', {'title': 'X', 'max_points': 1}).status_code, 403)
        self.assertEqual(self.patch(self.student, 'rubric', criterion, {'title': 'X'}).status_code, 403)
        self.assertEqual(self.as_user(self.student).delete(self.url('rubric', criterion)).status_code, 403)

    def test_other_course_instructor_cannot_read_or_change_the_rubric(self):
        self.assertEqual(self.as_user(self.other_teacher).get(self.url('rubric')).status_code, 403)
        self.assertEqual(self.post(self.other_teacher, 'rubric', {'title': 'X', 'max_points': 1}).status_code, 403)

    def test_criterion_is_not_found_through_another_assignment(self):
        other_assignment = self.make(Assignment.Status.DRAFT)
        criterion = self.criterion(assignment=other_assignment)

        response = self.patch(self.teacher, 'rubric', criterion, {'title': 'X'})

        self.assertEqual(response.status_code, 404)

    def test_archived_assignment_rubric_is_frozen(self):
        criterion = self.criterion()
        self.assignment.status = Assignment.Status.ARCHIVED
        self.assignment.save()

        self.assertEqual(self.post(self.teacher, 'rubric', {'title': 'X', 'max_points': 1}).status_code, 400)
        self.assertEqual(self.patch(self.teacher, 'rubric', criterion, {'title': 'X'}).status_code, 400)
        self.assertEqual(self.as_user(self.teacher).delete(self.url('rubric', criterion)).status_code, 400)

    # Test cases

    def test_instructor_adds_a_hidden_test_by_default(self):
        criterion = self.criterion()

        response = self.post(
            self.teacher,
            'tests',
            {
                'name': 'Big numbers',
                'stdin_input': '1000 2000\n',
                'expected_output': '3000\n',
                'criterion': criterion.id,
            },
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['visibility'], 'hidden')
        self.assertEqual(body['criterion'], criterion.id)
        self.assertEqual(body['time_limit_ms'], 2000)

    def test_test_input_and_output_keep_their_whitespace(self):
        response = self.post(
            self.teacher, 'tests', {'name': 'Spaces', 'stdin_input': '  1 2\n', 'expected_output': ' 3\n\n'}
        )

        self.assertEqual(response.json()['stdin_input'], '  1 2\n')
        self.assertEqual(response.json()['expected_output'], ' 3\n\n')

    def test_time_limit_is_capped(self):
        response = self.post(self.teacher, 'tests', {'name': 'Slow', 'time_limit_ms': 60_000})

        self.assertEqual(response.status_code, 400)
        self.assertIn('time_limit_ms', response.json())

    def test_test_cannot_use_a_criterion_from_another_assignment(self):
        foreign = self.criterion(assignment=self.make(Assignment.Status.DRAFT))

        response = self.post(self.teacher, 'tests', {'name': 'X', 'criterion': foreign.id})

        self.assertEqual(response.status_code, 400)
        self.assertIn('criterion', response.json())

    def test_instructor_edits_unlinks_and_deletes_a_test(self):
        test_case = self.test_case(criterion=self.criterion())

        edited = self.patch(self.teacher, 'tests', test_case, {'visibility': 'hidden', 'criterion': None})
        deleted = self.as_user(self.teacher).delete(self.url('tests', test_case))

        self.assertEqual(edited.json()['visibility'], 'hidden')
        self.assertIsNone(edited.json()['criterion'])
        self.assertEqual(deleted.status_code, 204)

    def test_instructor_sees_hidden_tests(self):
        self.test_case('Example')
        self.test_case('Secret', TestCaseModel.Visibility.HIDDEN, stdin_input='7 8', expected_output='15')

        names = [t['name'] for t in self.as_user(self.teacher).get(self.url('tests')).json()]

        self.assertEqual(names, ['Example', 'Secret'])

    def test_student_sees_only_public_tests_without_hidden_data(self):
        self.test_case('Example', stdin_input='1 2', expected_output='3')
        self.test_case(
            'Secret', TestCaseModel.Visibility.HIDDEN, stdin_input='SECRET-IN', expected_output='SECRET-OUT'
        )

        response = self.as_user(self.student).get(self.url('tests'))

        self.assertEqual(response.status_code, 200)
        [public] = response.json()
        self.assertEqual(set(public), {'id', 'name', 'stdin_input', 'expected_output'})
        self.assertEqual(public['name'], 'Example')
        self.assertEqual((public['stdin_input'], public['expected_output']), ('1 2', '3'))
        for secret in ('Secret', 'SECRET-IN', 'SECRET-OUT'):
            self.assertNotIn(secret, response.content.decode())

    def test_student_cannot_change_tests(self):
        test_case = self.test_case()

        self.assertEqual(self.post(self.student, 'tests', {'name': 'X'}).status_code, 403)
        self.assertEqual(self.patch(self.student, 'tests', test_case, {'name': 'X'}).status_code, 403)
        self.assertEqual(self.as_user(self.student).delete(self.url('tests', test_case)).status_code, 403)

    def test_student_cannot_read_a_draft_assignments_rubric_or_tests(self):
        draft = self.make(Assignment.Status.DRAFT)

        for kind in ('rubric', 'tests'):
            response = self.as_user(self.student).get(self.url(kind, assignment=draft))
            self.assertEqual(response.status_code, 404)

    def test_instructor_can_prepare_a_draft(self):
        draft = self.make(Assignment.Status.DRAFT)

        response = self.post(self.teacher, 'tests', {'name': 'Example'}, assignment=draft)

        self.assertEqual(response.status_code, 201)

    def test_test_is_not_found_through_another_course(self):
        test_case = self.test_case()
        foreign_assignment = self.make(Assignment.Status.PUBLISHED, course=self.other_course)
        url = f'/courses/{self.other_course.id}/assignments/{foreign_assignment.id}/tests/{test_case.id}'

        response = self.as_user(self.other_teacher).patch(url, {'name': 'X'}, content_type='application/json')

        self.assertEqual(response.status_code, 404)
