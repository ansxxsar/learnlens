from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework.throttling import ScopedRateThrottle

from accounts.roles import get_account_type
from courses.models import Course, CourseSection, Enrollment
from courses.permissions import get_course_role

PASSWORD = 'correct-horse-battery'


class AuthTestCase(APITestCase):
    def setUp(self):
        cache.clear()  # sign-in rate limit counters live in the cache
        self.user = get_user_model().objects.create_user(
            email='student@example.com', full_name='Test Student', password=PASSWORD
        )

    def sign_in(self, client=None, email='student@example.com', password=PASSWORD):
        client = client or self.client
        return client.post(reverse('auth-sign-in'), {'email': email, 'password': password}, format='json')


class SignInTests(AuthTestCase):
    def test_valid_credentials_start_a_session(self):
        response = self.sign_in()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'student@example.com')
        self.assertEqual(self.client.get(reverse('auth-me')).status_code, 200)

    def test_email_domain_case_is_ignored_like_at_account_creation(self):
        self.assertEqual(self.sign_in(email='student@EXAMPLE.com').status_code, 200)

    def test_all_credential_failures_look_the_same(self):
        wrong_password = self.sign_in(password='wrong-password')
        unknown_email = self.sign_in(email='nobody@example.com')
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        inactive = self.sign_in()

        for response in (wrong_password, unknown_email, inactive):
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.data, wrong_password.data)
        self.assertFalse(Session.objects.exists())

    def test_missing_fields_are_rejected(self):
        response = self.client.post(reverse('auth-sign-in'), {'email': 'student@example.com'}, format='json')

        self.assertEqual(response.status_code, 400)

    def test_csrf_token_is_required(self):
        client = APIClient(enforce_csrf_checks=True)

        self.assertEqual(self.sign_in(client).status_code, 403)
        self.assertFalse(Session.objects.exists())

    def test_sign_in_works_with_token_from_csrf_endpoint(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.get(reverse('auth-csrf')).status_code, 204)
        token = client.cookies['csrftoken'].value

        response = client.post(
            reverse('auth-sign-in'),
            {'email': 'student@example.com', 'password': PASSWORD},
            format='json',
            headers={'X-CSRFToken': token},
        )

        self.assertEqual(response.status_code, 200)

    def test_repeated_attempts_are_rate_limited(self):
        with mock.patch.dict(ScopedRateThrottle.THROTTLE_RATES, {'sign_in': '2/minute'}):
            self.sign_in(password='wrong-password')
            self.sign_in(password='wrong-password')
            # Blocked even with the right password.
            self.assertEqual(self.sign_in().status_code, 429)


class RegisterTests(AuthTestCase):
    def register(self, client=None, **overrides):
        data = {'full_name': 'New Student', 'email': '251122001@sdu.edu.kz', 'password': PASSWORD, **overrides}
        return (client or self.client).post(reverse('auth-register'), data, format='json')

    def test_register_creates_account_and_starts_session(self):
        response = self.register()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['email'], '251122001@sdu.edu.kz')
        self.assertEqual(response.data['enrollments'], [])
        self.assertNotIn('password', response.data)
        self.assertEqual(self.client.get(reverse('auth-me')).data['email'], '251122001@sdu.edu.kz')
        self.assertTrue(get_user_model().objects.get(email='251122001@sdu.edu.kz').check_password(PASSWORD))

    def test_new_account_can_sign_in_later(self):
        self.register()
        self.client.post(reverse('auth-sign-out'))

        self.assertEqual(self.sign_in(email='251122001@sdu.edu.kz').status_code, 200)

    def test_only_sdu_emails_can_register(self):
        for email in (
            'someone@gmail.com',
            'someone@notsdu.edu.kz',
            'someone@sdu.edu.kz.evil.com',
            'someone@mail.sdu.edu.kz',
        ):
            with self.subTest(email=email):
                response = self.register(email=email)

                self.assertEqual(response.status_code, 400)
                self.assertIn('email', response.data)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_email_domain_case_does_not_matter(self):
        self.assertEqual(self.register(email='251122001@SDU.EDU.KZ').status_code, 201)

    def test_number_email_registers_as_student(self):
        self.assertEqual(self.register().data['account_type'], 'student')

    def test_name_email_waits_for_approval_with_no_course_access(self):
        response = self.register(email='aigerim.teacher@sdu.edu.kz')

        self.assertEqual(response.data['account_type'], 'pending_teacher')
        self.assertEqual(response.data['enrollments'], [])

    def test_request_cannot_choose_its_own_account_type(self):
        response = self.register(email='aigerim.teacher@sdu.edu.kz', account_type='teacher', role='instructor')

        self.assertEqual(response.data['account_type'], 'pending_teacher')

    def test_request_cannot_make_itself_admin(self):
        self.assertEqual(self.register(is_admin=True, is_active=False).status_code, 201)

        user = get_user_model().objects.get(email='251122001@sdu.edu.kz')
        self.assertFalse(user.is_admin)
        self.assertTrue(user.is_active)

    def test_duplicate_email_is_rejected_regardless_of_case(self):
        get_user_model().objects.create_user(email='taken@sdu.edu.kz', full_name='Taken', password=PASSWORD)

        response = self.register(email='TAKEN@sdu.edu.kz')

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
        self.assertEqual(get_user_model().objects.count(), 2)

    def test_simultaneous_duplicate_is_rejected_without_a_server_error(self):
        with mock.patch('accounts.serializers.User.objects.create_user', side_effect=IntegrityError):
            response = self.register()

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_weak_password_is_rejected(self):
        response = self.register(password='12345')

        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.data)
        self.assertFalse(get_user_model().objects.filter(email='251122001@sdu.edu.kz').exists())

    def test_missing_name_is_rejected(self):
        self.assertEqual(self.register(full_name='').status_code, 400)

    def test_csrf_token_is_required(self):
        self.assertEqual(self.register(APIClient(enforce_csrf_checks=True)).status_code, 403)
        self.assertFalse(get_user_model().objects.filter(email='251122001@sdu.edu.kz').exists())

    def test_repeated_attempts_are_rate_limited(self):
        with mock.patch.dict(ScopedRateThrottle.THROTTLE_RATES, {'register': '1/minute'}):
            # A new client each time: registering signs in, and the throttle counts
            # signed-in users separately from anonymous visitors.
            self.register(APIClient())
            self.assertEqual(self.register(APIClient(), email='251122002@sdu.edu.kz').status_code, 429)


class AccountTypeTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.course = Course.objects.create(code='CS101', title='Intro to Programming', term='Fall 2026')

    def account_type(self, email, role=None, **extra):
        user = get_user_model().objects.create_user(email=email, full_name='Test', password=PASSWORD, **extra)
        if role:
            Enrollment.objects.create(user=user, course=self.course, role=role)
        return get_account_type(user)

    def test_instructor_enrollment_approves_a_teacher(self):
        self.assertEqual(self.account_type('teacher@sdu.edu.kz', Enrollment.Role.INSTRUCTOR), 'teacher')

    def test_teaching_assistant_with_number_email_is_a_teacher(self):
        self.assertEqual(self.account_type('251122003@sdu.edu.kz', Enrollment.Role.INSTRUCTOR), 'teacher')

    def test_student_with_name_email_stops_waiting_once_enrolled(self):
        self.assertEqual(self.account_type('student.name@sdu.edu.kz', Enrollment.Role.STUDENT), 'student')

    def test_admin_is_not_left_waiting(self):
        self.assertEqual(self.account_type('admin@gmail.com', is_admin=True), 'admin')

    def test_name_email_alone_gives_no_course_permission(self):
        user = get_user_model().objects.create_user(email='teacher@sdu.edu.kz', full_name='T', password=PASSWORD)

        self.assertIsNone(get_course_role(user, self.course.id))

    def test_admin_filter_lists_only_accounts_waiting_for_approval(self):
        waiting = get_user_model().objects.create_user(email='teacher@sdu.edu.kz', full_name='T', password=PASSWORD)
        get_user_model().objects.create_user(email='251122004@sdu.edu.kz', full_name='S', password=PASSWORD)
        approved = get_user_model().objects.create_user(email='prof@sdu.edu.kz', full_name='P', password=PASSWORD)
        Enrollment.objects.create(user=approved, course=self.course, role=Enrollment.Role.INSTRUCTOR)
        get_user_model().objects.create_superuser(email='admin@sdu.edu.kz', full_name='A', password=PASSWORD)
        self.client.force_login(get_user_model().objects.get(email='admin@sdu.edu.kz'))

        response = self.client.get('/admin/accounts/user/', {'teacher_approval': 'waiting'})

        self.assertEqual(response.status_code, 200)
        # self.user (student@example.com) from setUp also has a name-based email.
        self.assertEqual(set(response.context['cl'].queryset), {waiting, self.user})


class SignOutTests(AuthTestCase):
    def test_sign_out_deletes_the_session_on_the_server(self):
        self.sign_in()
        session_cookie = self.client.cookies['sessionid'].value

        self.assertEqual(self.client.post(reverse('auth-sign-out')).status_code, 204)

        self.assertFalse(Session.objects.filter(session_key=session_cookie).exists())
        # Replaying the old cookie must not work.
        replay = APIClient()
        replay.cookies['sessionid'] = session_cookie
        self.assertEqual(replay.get(reverse('auth-me')).status_code, 401)

    def test_sign_out_requires_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)

        self.assertEqual(client.post(reverse('auth-sign-out')).status_code, 403)
        self.assertEqual(client.get(reverse('auth-me')).status_code, 200)

    def test_anonymous_sign_out_is_rejected(self):
        self.assertEqual(self.client.post(reverse('auth-sign-out')).status_code, 401)


class MeTests(AuthTestCase):
    def test_anonymous_request_gets_401(self):
        self.assertEqual(self.client.get(reverse('auth-me')).status_code, 401)

    def test_deactivated_user_loses_existing_session(self):
        self.sign_in()
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)

        self.assertEqual(self.client.get(reverse('auth-me')).status_code, 401)

    def test_returns_only_own_profile_and_course_roles(self):
        course = Course.objects.create(code='CS101', title='Intro to Programming', term='Fall 2026')
        section = CourseSection.objects.create(course=course, code='A')
        taught = Course.objects.create(code='CS201', title='Algorithms', term='Fall 2026')
        Enrollment.objects.create(user=self.user, course=course, section=section)
        Enrollment.objects.create(user=self.user, course=taught, role=Enrollment.Role.INSTRUCTOR)
        other_user = get_user_model().objects.create_user(
            email='other@example.com', full_name='Other Student', password=PASSWORD
        )
        Enrollment.objects.create(user=other_user, course=course)
        self.sign_in()

        response = self.client.get(reverse('auth-me'))

        self.assertEqual(
            response.json(),
            {
                'id': self.user.id,
                'email': 'student@example.com',
                'full_name': 'Test Student',
                'is_admin': False,
                'account_type': 'teacher',
                'enrollments': [
                    {
                        'course_id': course.id,
                        'course_code': 'CS101',
                        'course_title': 'Intro to Programming',
                        'section_code': 'A',
                        'role': 'student',
                    },
                    {
                        'course_id': taught.id,
                        'course_code': 'CS201',
                        'course_title': 'Algorithms',
                        'section_code': None,
                        'role': 'instructor',
                    },
                ],
            },
        )
