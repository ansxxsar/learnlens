from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework.throttling import ScopedRateThrottle

from courses.models import Course, CourseSection, Enrollment

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
